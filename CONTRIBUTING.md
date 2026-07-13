# Contributing to SLIC

Thank you for your interest in SLIC. Contributions that improve the software
for the research community are welcome.

## Who can contribute

SLIC is research software maintained at the University of Sheffield. External
contributions are accepted but please open an issue to discuss significant
changes before investing time in an implementation - we want to make sure
proposed changes align with the research goals of the project.

## Before you start

- Read the [LICENSE](LICENSE) - contributions are accepted on the understanding
  that they will be distributed under the same non-commercial research license.
- Read the [Code of Conduct](CODE_OF_CONDUCT.md).
- Check the [Architecture docs](docs/architecture.md) to understand how the
  application is structured before making changes.

## How to report a bug

Use the in-app bug report form at `/bug-report/` or open a GitHub issue.
Include:
- Steps to reproduce
- Expected behaviour
- Actual behaviour
- Browser and OS if it is a front-end issue

Do not include any participant data or personally identifiable information
in bug reports.

## How to suggest a feature

Open a GitHub issue with the label `enhancement`. Describe the research use
case that motivates the feature - this helps us understand whether it is in
scope.

## Development workflow

1. Fork the repository and create a branch from `main`.
2. Follow the [setup guide](docs/setup.md) to get a local environment running.
3. Make your changes. Write or update tests - the test suite must pass before
   a pull request will be reviewed.
4. Run the tests:
   ```bash
   pytest tests/unit/
   pytest tests/          # includes integration tests
   ```
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
   format: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, etc.
6. Open a pull request against `main`. Describe what changed and why.

## Sensitive data

SLIC handles encrypted participant data. Take care with any changes that touch:
- `responses/models.py` (ParticipantId, ClickResponse encryption)
- `accounts/models.py` (user PII encryption and blind index)
- The `FIELD_ENCRYPTION_KEY` or `BLIND_INDEX_KEY` settings

Never commit real encryption keys, participant data, or database dumps.
The `.gitignore` excludes `*.dump` for this reason.

## Questions

Contact Dr Chris Montgomery - c.montgomery@sheffield.ac.uk
