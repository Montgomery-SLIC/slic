"""
migrate_from_rails - Step 3 of the SLIC Rails->Django port.

Reads the Rails PostgreSQL database, decrypts all Lockbox-encrypted fields,
re-encrypts with django-encrypted-model-fields (Fernet), remaps acts_as /
actable_id task IDs to Django MTI IDs, and inserts everything into the Django
database in a single atomic transaction.

Usage
-----
    python manage.py migrate_from_rails [--dry-run] [--clear]

    RAILS_DSN and LOCKBOX_KEY are read from .env automatically.

Prerequisites
-------------
    python manage.py migrate        # Django schema must already exist
    FIELD_ENCRYPTION_KEY, BLIND_INDEX_KEY, RAILS_DSN, LOCKBOX_KEY set in .env

Audio / transcript files
------------------------
This command migrates database rows only.  Copy Rails ActiveStorage blobs
separately (Step 3b), then run fix_audio_paths to update SampleTask paths.

    # On the VM, Rails stores blobs under storage/ (disk service):
    scp -r user@slic.shef.ac.uk:/var/www/slic/current/storage/ django_app/media/

Schema assumptions
------------------
Verified against the 2026-07 pg_dump.  If a column is absent the command
will raise a clear KeyError before committing anything to Django.

Verify the following against \\d <table> on the VM if in doubt:
  - experiments: user_id (confirmed), name (confirmed, not title)
  - intermediate_screen_tasks: message column (confirmed - same in Rails and Django)
  - question responses table name: responses (confirmed, not question_responses)
  - participant_ids table name: participant_ids (not participants / respondents)
"""

import base64
import datetime
import hashlib
import hmac as _hmac
import logging
import os

import psycopg2
import psycopg2.extras
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection as dj_conn, transaction

from accounts.models import User, ResearcherInvitation
from experiments.models import Experiment
from tasks.models import (
    Task, QuestionTask, SampleTask, ListeningTask, ClickTask,
    IntermediateScreenTask, Question, Option, Scale, RAILS_STI_TYPE_MAP,
)
from responses.models import Visit, ParticipantId, Response, ClickResponse

log = logging.getLogger(__name__)


# ── Lockbox decryption ────────────────────────────────────────────────────────

def _lb_key(master_hex: str, table: str, column: str) -> bytes:
    """Derive per-attribute AES-256 key matching Lockbox 0.4.9 KeyGenerator.
    Salt = table name; info = b'\xb4'*32 + column name (e.g. 'email_ciphertext').
    Lockbox uses the full DB column name, NOT the stripped attribute name."""
    hkdf = HKDF(
        algorithm=hashes.SHA384(),
        length=32,
        salt=table.encode(),
        info=b'\xb4' * 32 + column.encode(),
        backend=default_backend(),
    )
    return hkdf.derive(bytes.fromhex(master_hex))


def _lb_decrypt(b64: str | None, key: bytes) -> str | None:
    """AES-256-GCM decrypt. Rails Lockbox format: base64(nonce[12] + ciphertext + tag[16])."""
    if not b64:
        return None
    raw = base64.b64decode(b64)
    nonce, payload = raw[:12], raw[12:]
    try:
        return AESGCM(key).decrypt(nonce, payload, None).decode('utf-8')
    except Exception as exc:
        raise ValueError(f'Lockbox decrypt failed: {exc}') from exc


def _bidx(email: str) -> str:
    key = bytes.fromhex(settings.BLIND_INDEX_KEY)
    return _hmac.new(key, email.lower().strip().encode('utf-8'), hashlib.sha256).hexdigest()


# ── Timestamp preservation ────────────────────────────────────────────────────

def _aware(dt):
    """Attach UTC tzinfo to naive datetimes returned by psycopg2 from the Rails DB."""
    if dt is None:
        return None
    if isinstance(dt, datetime.datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def _stamp(model_cls, pk, **fields):
    """Overwrite auto_now / auto_now_add timestamps with the original Rails values.
    update() bypasses auto_now, so this is the only reliable approach."""
    updates = {k: _aware(v) for k, v in fields.items() if v is not None}
    if updates:
        model_cls.objects.filter(pk=pk).update(**updates)


# ── MTI child-table insert (raw SQL avoids Django MTI save() ambiguity) ───────

def _insert_child(table: str, **fields):
    cols = ', '.join(fields)
    placeholders = ', '.join(['%s'] * len(fields))
    with dj_conn.cursor() as cur:
        cur.execute(
            f'INSERT INTO {table} ({cols}) VALUES ({placeholders})',
            list(fields.values()),
        )


# ── Management command ────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Migrate data from the Rails PostgreSQL database to Django (Step 3)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rails-dsn', default=os.environ.get('RAILS_DSN', ''),
            help='psycopg2 DSN for the Rails DB (or set RAILS_DSN in .env)',
        )
        parser.add_argument(
            '--lockbox-key', default=os.environ.get('LOCKBOX_KEY', ''),
            help='Lockbox master key: 64-char hex string (or set LOCKBOX_KEY in .env)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Read and decrypt every row without writing anything to Django',
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete all existing Django rows before migrating (use on empty DB only)',
        )

    def handle(self, *args, **options):
        if not settings.FIELD_ENCRYPTION_KEY:
            raise CommandError('FIELD_ENCRYPTION_KEY is not set - cannot re-encrypt migrated data')
        if not settings.BLIND_INDEX_KEY:
            raise CommandError('BLIND_INDEX_KEY is not set - cannot compute email blind indices')

        if not options['rails_dsn']:
            raise CommandError('RAILS_DSN not set - add it to .env or pass --rails-dsn')
        if not options['lockbox_key']:
            raise CommandError('LOCKBOX_KEY not set - add it to .env or pass --lockbox-key')

        master = options['lockbox_key'].strip()
        if len(master) != 64:
            raise CommandError(f'LOCKBOX_KEY must be 64 hex chars (got {len(master)})')

        dry = options['dry_run']
        prefix = '[DRY RUN] ' if dry else ''
        self.out(f'{prefix}Connecting to Rails DB…')

        try:
            rails = psycopg2.connect(options['rails_dsn'])
        except psycopg2.Error as exc:
            raise CommandError(f'Rails DB connection failed: {exc}')

        rails.autocommit = True  # read-only; autocommit avoids stale-snapshot issues
        cur = rails.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SET default_transaction_read_only = on')

        try:
            if options['clear'] and not dry:
                self._clear_all()

            with transaction.atomic():
                user_map = self._users(cur, master, dry)
                self._invitations(cur, user_map, dry)
                exp_map = self._experiments(cur, user_map, dry)
                task_map, qt_map, ct_map = self._tasks(cur, exp_map, dry)
                q_map = self._questions(cur, qt_map, dry)
                self._participants(cur, exp_map, master, dry)
                self._visits(cur, task_map, dry)
                self._responses(cur, q_map, ct_map, dry)
        finally:
            cur.close()
            rails.close()

        self.out(self.style.SUCCESS(
            f'{prefix}Migration complete - '
            'run fix_audio_paths after copying Rails storage/ files.'
            if not dry else
            f'{prefix}Dry run complete - no data written.'
        ))

    # ── helpers ──────────────────────────────────────────────────────────────

    def out(self, msg):
        self.stdout.write(msg)

    def warn(self, msg):
        self.stdout.write(self.style.WARNING(msg))

    def _clear_all(self):
        self.out('Clearing existing Django data…')
        # FK order: children before parents
        ClickResponse.objects.all().delete()
        Response.objects.all().delete()
        Visit.objects.all().delete()
        ParticipantId.objects.all().delete()
        Scale.objects.all().delete()
        Option.objects.all().delete()
        Question.objects.all().delete()
        Task.objects.all().delete()       # MTI cascade deletes all child rows
        Experiment.objects.all().delete()
        ResearcherInvitation.objects.all().delete()
        User.objects.all().delete()

    # ── section migrations ────────────────────────────────────────────────────

    def _users(self, cur, master, dry):
        """Decrypt Lockbox PII, re-encrypt via EncryptedTextField, compute HMAC bidx.
        Returns {rails_user_id: django_user_id}."""
        attrs = ('email', 'name', 'institution', 'country', 'faculty', 'research_level')
        # Lockbox uses the full column name (with _ciphertext suffix) in its HKDF info
        keys = {a: _lb_key(master, 'users', f'{a}_ciphertext') for a in attrs}

        cur.execute('SELECT * FROM users ORDER BY id')
        rows = cur.fetchall()
        self.out(f'  Users: {len(rows)}')

        user_map = {}
        for row in rows:
            def dec(attr):
                return _lb_decrypt(row.get(f'{attr}_ciphertext'), keys[attr])

            email = dec('email')
            if not email:
                self.warn(f"  User {row['id']}: email blank or undecryptable - skipped")
                continue

            if dry:
                self.out(f"  [DRY] User {row['id']}: {email}")
                continue

            u = User(
                admin=bool(row.get('admin', False)),
                is_staff=bool(row.get('is_staff', False)),
                is_active=bool(row.get('is_active', True)),
                funded=row.get('funded'),
                mailing_list=row.get('mailing_list'),
                failed_attempts=row.get('failed_attempts') or 0,
                locked_at=_aware(row.get('locked_at')),
                sign_in_count=row.get('sign_in_count') or 0,
                current_sign_in_at=_aware(row.get('current_sign_in_at')),
                last_sign_in_at=_aware(row.get('last_sign_in_at')),
                current_sign_in_ip=row.get('current_sign_in_ip'),
                last_sign_in_ip=row.get('last_sign_in_ip'),
                reset_password_token=row.get('reset_password_token'),
                reset_password_sent_at=_aware(row.get('reset_password_sent_at')),
                remember_created_at=_aware(row.get('remember_created_at')),
                unlock_token=row.get('unlock_token'),
            )
            # email property setter encrypts + computes bidx
            u.email = email
            # Remaining encrypted PII - set plaintext; EncryptedTextField encrypts on save
            u.name_ciphertext = dec('name')
            u.institution_ciphertext = dec('institution')
            u.country_ciphertext = dec('country')
            u.faculty_ciphertext = dec('faculty')
            u.research_level_ciphertext = dec('research_level')
            # Researchers must use "forgot password" after migration.
            # Rails Devise bcrypt ($2a$) is not compatible with Django's BCryptSHA256PasswordHasher.
            u.password = '!'
            u.save()
            _stamp(User, u.pk, date_joined=row.get('created_at'))
            user_map[row['id']] = u.pk

        self.out(f'    -> {len(user_map)} migrated')
        return user_map

    def _invitations(self, cur, user_map, dry):
        cur.execute('SELECT * FROM researcher_invitations ORDER BY id')
        rows = cur.fetchall()
        self.out(f'  Invitations: {len(rows)}')
        if dry:
            return
        for row in rows:
            inv = ResearcherInvitation(
                registration_code=row['registration_code'],
                used=bool(row.get('used', False)),
                user_id=user_map.get(row.get('user_id')),
            )
            inv.save()
            _stamp(ResearcherInvitation, inv.pk,
                   created_at=row.get('created_at'), updated_at=row.get('updated_at'))

    def _experiments(self, cur, user_map, dry):
        """Returns {rails_experiment_id: django_experiment_id}."""
        cur.execute('SELECT * FROM experiments ORDER BY id')
        rows = cur.fetchall()
        self.out(f'  Experiments: {len(rows)}')
        exp_map = {}
        if dry:
            return exp_map

        for row in rows:
            owner = user_map.get(row.get('user_id'))
            if not owner:
                self.warn(f"  Experiment {row['id']}: owner not in user_map - skipped")
                continue
            e = Experiment(
                user_id=owner,
                name=row.get('name') or row.get('title') or '',
                description=row.get('description') or '',
                complete=bool(row.get('complete', False)),
                slug=row['slug'],
                terms=row.get('terms') or '',
            )
            e.save()
            _stamp(Experiment, e.pk,
                   created_at=row.get('created_at'), updated_at=row.get('updated_at'))
            exp_map[row['id']] = e.pk

        self.out(f'    -> {len(exp_map)} migrated')
        return exp_map

    def _tasks(self, cur, exp_map, dry):
        """
        Maps Rails acts_as task IDs to Django MTI IDs.

        In Rails: tasks.actable_type='ClickTask', tasks.actable_id=3 (in click_tasks table)
        In Django: Task.pk == ClickTask.task_ptr_id (single shared sequence)

        Returns:
            task_map - {rails_task_id: django_task_id}
            qt_map   - {rails_question_task_id: django_task_id}
            ct_map   - {rails_click_task_id: django_task_id}
        """
        cur.execute('SELECT * FROM tasks ORDER BY id')
        all_tasks = cur.fetchall()

        def fetch_type_table(table):
            cur.execute(f'SELECT * FROM {table}')
            return {r['id']: dict(r) for r in cur.fetchall()}

        qt_rows  = fetch_type_table('question_tasks')
        st_rows  = fetch_type_table('sample_tasks')
        lt_rows  = fetch_type_table('listening_tasks')
        ct_rows  = fetch_type_table('click_tasks')
        ist_rows = fetch_type_table('intermediate_screen_tasks')

        self.out(
            f'  Tasks: {len(all_tasks)} base '
            f'({len(qt_rows)} Q, {len(st_rows)} S, {len(lt_rows)} L, '
            f'{len(ct_rows)} C, {len(ist_rows)} I)'
        )

        task_map, qt_map, ct_map, st_map = {}, {}, {}, {}

        if dry:
            return task_map, qt_map, ct_map

        # Two passes: top-level tasks first so SampleTask parents exist for sub-tasks
        top  = [r for r in all_tasks if r['taskable_type'] == 'Experiment']
        subs = [r for r in all_tasks if r['taskable_type'] == 'SampleTask']

        for pass_rows in (top, subs):
            for row in pass_rows:
                atype = row['actable_type']
                aid   = row['actable_id']

                if row['taskable_type'] == 'SampleTask':
                    parent_id = st_map.get(row['taskable_id'])
                    if parent_id is None:
                        self.warn(f"  Task {row['id']}: parent SampleTask {row['taskable_id']} missing - skipped")
                        continue
                    owner = dict(sample_task_id=parent_id, experiment_id=None)
                else:
                    parent_id = exp_map.get(row['taskable_id'])
                    if parent_id is None:
                        self.warn(f"  Task {row['id']}: parent Experiment {row['taskable_id']} missing - skipped")
                        continue
                    owner = dict(experiment_id=parent_id, sample_task_id=None)

                task = Task(
                    name=row.get('name') or atype,
                    sort=row.get('sort'),
                    random=bool(row.get('random', False)),
                    **owner,
                )
                task.save()
                _stamp(Task, task.pk,
                       created_at=row.get('created_at'), updated_at=row.get('updated_at'))
                task_map[row['id']] = task.pk

                if atype == 'QuestionTask':
                    _insert_child('question_tasks', task_ptr_id=task.pk)
                    qt_map[aid] = task.pk

                elif atype == 'SampleTask':
                    sr = st_rows.get(aid, {})
                    _insert_child('sample_tasks',
                                  task_ptr_id=task.pk,
                                  calibration=bool(sr.get('calibration', False)),
                                  audio='',       # filled by fix_audio_paths (Step 3b)
                                  transcript='')
                    st_map[aid] = task.pk

                elif atype == 'ListeningTask':
                    lr = lt_rows.get(aid, {})
                    _insert_child('listening_tasks',
                                  task_ptr_id=task.pk,
                                  listens=lr.get('listens') or 1)

                elif atype == 'ClickTask':
                    cr = ct_rows.get(aid, {})
                    _insert_child('click_tasks',
                                  task_ptr_id=task.pk,
                                  prompt=cr.get('prompt') or '',
                                  explanation_prompt=cr.get('explanation_prompt') or '')
                    ct_map[aid] = task.pk

                elif atype == 'IntermediateScreenTask':
                    ir = ist_rows.get(aid, {})
                    _insert_child('intermediate_screen_tasks',
                                  task_ptr_id=task.pk,
                                  message=ir.get('message') or '')

                else:
                    self.warn(f"  Task {row['id']}: unknown actable_type '{atype}' - base Task only")

        self.out(f'    -> {len(task_map)} tasks ({len(qt_map)} Q, {len(ct_map)} C)')
        return task_map, qt_map, ct_map

    def _questions(self, cur, qt_map, dry):
        """Returns {rails_question_id: django_question_id}."""
        cur.execute('SELECT * FROM questions ORDER BY id')
        q_rows = cur.fetchall()
        cur.execute('SELECT * FROM options ORDER BY id')
        opt_rows = cur.fetchall()
        cur.execute('SELECT * FROM scales ORDER BY id')
        scale_rows = cur.fetchall()

        self.out(f'  Questions: {len(q_rows)}, Options: {len(opt_rows)}, Scales: {len(scale_rows)}')
        q_map = {}
        if dry:
            return q_map

        for row in q_rows:
            qt_django = qt_map.get(row['question_task_id'])
            if qt_django is None:
                self.warn(f"  Question {row['id']}: QuestionTask not in qt_map - skipped")
                continue
            rails_type = row.get('type') or ''
            q = Question(
                question_task_id=qt_django,
                question_type=RAILS_STI_TYPE_MAP.get(rails_type, 'text'),
                prompt=row.get('prompt') or '',
                sort=row.get('sort'),
                required=bool(row.get('required', False)),
            )
            q.save()
            _stamp(Question, q.pk,
                   created_at=row.get('created_at'), updated_at=row.get('updated_at'))
            q_map[row['id']] = q.pk

        # options uses a polymorphic FK: chooseable_type/chooseable_id
        for row in opt_rows:
            if row.get('chooseable_type') != 'Question':
                continue
            q_django = q_map.get(row['chooseable_id'])
            if q_django is None:
                continue
            opt = Option(question_id=q_django, contents=row.get('contents') or '')
            opt.save()
            _stamp(Option, opt.pk,
                   created_at=row.get('created_at'), updated_at=row.get('updated_at'))

        # scales uses rating_id as the FK to questions
        for row in scale_rows:
            q_django = q_map.get(row['rating_id'])
            if q_django is None:
                continue
            sc = Scale(
                question_id=q_django,
                bins=row['bins'],
                low=row.get('low') or '',
                high=row.get('high') or '',
            )
            sc.save()
            _stamp(Scale, sc.pk,
                   created_at=row.get('created_at'), updated_at=row.get('updated_at'))

        self.out(f'    -> {len(q_map)} questions migrated')
        return q_map

    def _participants(self, cur, exp_map, master, dry):
        # Try the table name used in the Rails schema; adjust if yours differs
        try:
            cur.execute('SELECT * FROM participant_ids ORDER BY id')
        except psycopg2.Error:
            raise CommandError(
                'Table participant_ids not found - check the actual Rails table name '
                'with \\dt on the VM and update this command accordingly.'
            )
        rows = cur.fetchall()
        self.out(f'  Participants: {len(rows)}')
        if dry:
            return

        # Lockbox uses full column name in HKDF info - try both possible table names
        email_key   = _lb_key(master, 'participant_ids', 'email_ciphertext')
        email_key_b = _lb_key(master, 'participants', 'email_ciphertext')

        count = 0
        for row in rows:
            exp_django = exp_map.get(row.get('experiment_id'))
            if exp_django is None:
                self.warn(f"  Participant {row['id']}: experiment not in exp_map - skipped")
                continue

            p = ParticipantId(
                experiment_id=exp_django,
                participant_id=row['participant_id'],
                slug=row.get('slug') or '',
            )
            raw_ct = row.get('email_ciphertext')
            if raw_ct:
                try:
                    email = _lb_decrypt(raw_ct, email_key)
                except Exception:
                    try:
                        email = _lb_decrypt(raw_ct, email_key_b)
                    except Exception:
                        email = None
                        self.warn(f"  Participant {row['id']}: email decrypt failed with both key derivations")
                if email:
                    p.email = email  # property setter encrypts + computes bidx
            p.save()
            _stamp(ParticipantId, p.pk,
                   created_at=row.get('created_at'), updated_at=row.get('updated_at'))
            count += 1

        self.out(f'    -> {count} migrated')

    def _visits(self, cur, task_map, dry):
        cur.execute('SELECT * FROM visits ORDER BY id')
        rows = cur.fetchall()
        self.out(f'  Visits: {len(rows)}')
        if dry:
            return

        count = 0
        for row in rows:
            django_task = task_map.get(row['task_id'])
            if django_task is None:
                continue
            # Rails may have duplicate (participant_id, task_id) pairs; use get_or_create
            v, created = Visit.objects.get_or_create(
                participant_id=row['participant_id'],
                task_id=django_task,
                defaults={'visited': bool(row.get('visited', False))},
            )
            if created:
                _stamp(Visit, v.pk,
                       created_at=row.get('created_at'), updated_at=row.get('updated_at'))
            count += 1

        self.out(f'    -> {count} migrated')

    def _responses(self, cur, q_map, ct_map, dry):
        # Question responses - Rails table may be 'responses' or 'question_responses'
        try:
            cur.execute('SELECT * FROM responses ORDER BY id')
        except psycopg2.Error:
            cur.execute('SELECT * FROM question_responses ORDER BY id')
        q_rows = cur.fetchall()

        cur.execute('SELECT * FROM click_responses ORDER BY id')
        cr_rows = cur.fetchall()

        self.out(f'  Responses: {len(q_rows)} question, {len(cr_rows)} click')
        if dry:
            return

        qcount = 0
        for row in q_rows:
            q_django = q_map.get(row.get('question_id'))
            if q_django is None:
                continue
            r = Response(
                participant_id=row['participant_id'],
                question_id=q_django,
            )
            # answer was plaintext in Rails; EncryptedTextField encrypts on save
            r.answer_ciphertext = row.get('answer') or ''
            r.save()
            _stamp(Response, r.pk,
                   created_at=row.get('created_at'), updated_at=row.get('updated_at'))
            qcount += 1

        ccount = 0
        for row in cr_rows:
            # Rails click_responses.click_task_id -> click_tasks.id (acts_as specific table)
            # ct_map maps that to the Django Task.pk (= ClickTask.task_ptr_id)
            django_ct = ct_map.get(row.get('click_task_id'))
            if django_ct is None:
                continue
            cr = ClickResponse(
                participant_id=row['participant_id'],
                click_task_id=django_ct,
                time=row.get('time'),
                no_clicks_explanation=bool(row.get('no_clicks_explanation', False)),
                from_checkbox=bool(row.get('from_checkbox', False)),
            )
            # answer was plaintext in Rails (GDPR gap); EncryptedTextField encrypts on save
            cr.answer_ciphertext = row.get('answer') or ''
            cr.save()
            _stamp(ClickResponse, cr.pk,
                   created_at=row.get('created_at'), updated_at=row.get('updated_at'))
            ccount += 1

        self.out(f'    -> {qcount} question responses, {ccount} click responses migrated')
