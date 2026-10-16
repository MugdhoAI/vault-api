# Contributing to Vault API

Thank you for considering a contribution to Vault API. Contributions may include bug fixes, tests, documentation improvements, and focused changes to the API or its security controls.

## Before you start

Check existing issues and pull requests before starting work. For a substantial change to authentication, authorization, encryption, configuration, database behavior, or the API contract, open an issue or discussion first so the approach can be reviewed.

## Development setup

Use Python 3.12 or newer and follow the setup and configuration instructions in the README.

1. Create and activate a virtual environment.
2. Install the project and development dependencies:

   ```bash
   python -m pip install -e ".[dev]"
   ```

3. Configure the environment using `.env.example` and the README. Use only local test credentials and a disposable development database.
4. Start the PostgreSQL service required by the tests. The repository includes a Docker Compose configuration:

   ```bash
   docker compose up -d db
   ```

5. Run the test suite and static checks:

   ```bash
   python -m pytest
   python -m ruff check .
   ```

Do not use production credentials, real secrets, or a database containing personal or sensitive data for development or tests.

## Security-sensitive changes

Changes to this project can affect access to stored secrets. Pull requests involving security behavior must include tests for the relevant success and failure paths.

- Preserve authentication requirements on protected endpoints.
- Preserve per-user ownership checks. Test that one user cannot list, retrieve, update, or delete another user's secrets.
- Do not store passwords in plain text or return secret values to an unauthorized caller.
- Do not log secret values, passwords, access tokens, encryption keys, or other credentials.
- Keep encryption and key-rotation behavior consistent with the documented configuration. Do not silently change how existing encrypted values are handled.
- Validate configuration safely and never introduce real credentials into source control, examples, fixtures, logs, or test output.
- When changing database models or persistence behavior, account for schema changes and existing data.
- Add regression tests for reported vulnerabilities and authorization failures, not only for the expected successful request.

Do not claim that a change makes the service production ready without evidence and corresponding documentation. The README describes current limitations that must remain accurate.

## Pull request expectations

A good pull request should:

- Explain the problem, the chosen solution, and any security implications.
- Stay focused and avoid unrelated refactoring.
- Include or update automated tests for behavior changes.
- Pass the relevant test suite and Ruff checks, or clearly document a reproducible blocker.
- Update the README when configuration, endpoints, security behavior, or limitations change.
- Avoid committing `.env` files, credentials, database dumps, generated artifacts, or personal data.
- Respect the project's MIT License and the licenses of third-party dependencies.

## Reporting bugs

Include reproduction steps, expected and actual behavior, and relevant sanitized error messages. For suspected security vulnerabilities, do not publish usable credentials, secret values, or exploit details in a public issue; contact the repository owner privately through an available GitHub contact method.

## License

By submitting a contribution, you agree that your contribution is provided under the project's [MIT License](LICENSE). You retain the copyright to your contribution, subject to the license terms.
