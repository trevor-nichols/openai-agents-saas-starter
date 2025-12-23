# CI Helper Scripts

These scripts provide lightweight local checks that mirror CI expectations.

- `check_workflows.py` — validates that GitHub Actions workflow YAML parses cleanly.
- `check_terraform_fmt.sh` — runs `terraform fmt -check` against `ops/infra` when Terraform is installed.

Usage:
```
python tools/ci/check_workflows.py
./tools/ci/check_terraform_fmt.sh
```
