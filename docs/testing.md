# Testing

The test suite has two layers:

| Layer | Location | Tool | Speed |
|-------|----------|------|-------|
| Unit | `tests/unit/` | pytest-django | Fast (no browser) |
| End-to-end | `tests/e2e/` | Playwright | Slow (real browser) |

## Running tests

No need to activate the venv - use `make` or `uv run` directly:

**Unit tests only (recommended during development):**

```bash
make test
# or: uv run pytest tests/unit/
```

**All tests (excluding e2e):**

```bash
make test-all
# or: uv run pytest tests/ --ignore=tests/e2e -q
```

**E2E tests (requires a running dev server and Playwright browsers):**

```bash
# Install browsers once
uv run playwright install chromium

uv run pytest tests/e2e/
```

## Unit test layout

```
tests/unit/
├── conftest.py          # shared fixtures (user, patch_blind_index_key)
├── test_models.py       # User model - email property, bidx, get_by_natural_key
├── test_forms.py        # ProfileEditForm - valid/invalid paths
├── test_views.py        # ProfileEditView, AccountDeleteView
└── test_backends.py     # HMACEmailBackend
```

### Key fixtures

**`user`** - creates a persisted `User` with `email='test@example.com'` and `password='correct-password'`. Available in all unit tests via `conftest.py`.

**`patch_blind_index_key`** - `autouse=True` fixture that sets `settings.BLIND_INDEX_KEY` to a fixed test value for every unit test. Without this, the `email_bidx` unique constraint would fail on the second user created (all bidx values would be `''`).

### Significant test cases

| File | Class / test | What it verifies |
|------|--------------|-----------------|
| `test_forms.py` | `TestProfileEditFormCurrentPassword` | Wrong/missing `current_password` fails validation |
| `test_forms.py` | `TestProfileEditFormPasswordChange` | Mismatched or missing confirmation rejects |
| `test_forms.py` | `TestProfileEditFormRequiredFields` | Each required field individually |
| `test_views.py` | `test_valid_post_updates_email_and_bidx` | Email setter updates both `email_ciphertext` and `email_bidx` |
| `test_views.py` | `test_wrong_current_password_does_not_save` | Failed auth doesn't persist partial changes |
| `test_views.py` | `TestAccountDeleteView` | Deletion, logout, and unauthenticated guard |
| `test_backends.py` | `test_correct_credentials_returns_user` | Full HMAC lookup + password check round-trip |
| `test_backends.py` | `test_inactive_user_returns_none` | Inactive accounts are rejected |
| `test_models.py` | `test_case_insensitive` | `_compute_bidx` normalises before hashing |
| `test_models.py` | `test_lookup_is_case_insensitive` | `get_by_natural_key` finds uppercase emails |

## E2E test layout

```
tests/e2e/
├── conftest.py              # researcher fixture, login() helper
├── test_static_pages.py
├── test_navigation.py
├── test_researcher_flow.py  # login, create/edit experiment, download
└── test_participant_flow.py # participant task sequence
```

The `login()` helper in `conftest.py` bypasses the allauth form using `Client.force_login()` and injects a session cookie into the Playwright browser context. This is necessary because the HMAC blind-index lookup requires a real `BLIND_INDEX_KEY` that may not be set in the CI environment.

## Settings used during tests

Both test layers use `slic.settings.development` (configured in `pytest.ini`). Unit tests override `BLIND_INDEX_KEY` via the `patch_blind_index_key` autouse fixture so database operations work without a real key in the environment.
