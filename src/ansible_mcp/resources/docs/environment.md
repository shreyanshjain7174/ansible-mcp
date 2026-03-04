# Environment Tools

## `ade_environment_info`

Returns a structured environment snapshot and a formatted summary, including:

- active or discoverable virtual environment
- Python version (`python3 --version`)
- Ansible version (`ansible --version`)
- ansible-lint version (`ansible-lint --version`)
- ADE/ADT availability
- installed collections (`ansible-galaxy collection list`)

## `adt_check_env`

Checks whether `ansible-dev-tools` is installed.

Installation fallback order:

1. `pip install ansible-dev-tools`
2. `pipx install ansible-dev-tools`

## `ade_setup_environment`

Sets up an Ansible development virtual environment and installs core tools.

Key inputs:

- `envName`, `pythonVersion`
- `collections`
- `installRequirements`, `requirementsFile`

Behavior:

- auto-detects OS/package-manager when explicit values are not supplied
- creates virtualenv
- installs ADT (or fallback lint/core packages)
- optionally installs collections and requirements
- performs final ansible-lint verification
