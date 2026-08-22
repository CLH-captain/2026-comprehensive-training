# Project Rules

- Follow `API -> Service/Statistics -> Repository -> Model -> MySQL`.
- MySQL is the only source for business records and statistics.
- Every database schema change must use Alembic.
- Dashboard, Statistics API, and Agent Tools must share Statistics services.
- Do not implement arbitrary Text-to-SQL in the MVP.
- Do not modify Hermes Core; isolate compatibility in the project adapter/plugin.
- Keep secrets in `.env`; never commit passwords, tokens, or API keys.
- Preserve RBAC in repository queries and Agent Tool calls.
- Use fixed-seed synthetic data only; never introduce real student records.
- Add tests for critical Services, Statistics, permissions, migrations, and APIs.
- Run the current phase tests plus existing regression tests before each commit.
- Keep every completed phase runnable; do not add non-functional placeholder code.
