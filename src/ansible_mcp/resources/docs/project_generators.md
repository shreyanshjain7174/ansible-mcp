# Project Generator Tools

## `ansible_create_playbook`

Creates a playbook project using `ansible-creator`:

`ansible-creator init playbook --no-overwrite <name> [--path <path>]`

Parameters:

- `name` (required)
- `path` (optional, workspace-relative)

## `ansible_create_collection`

Creates a collection project using `ansible-creator`:

`ansible-creator init collection --no-overwrite <name> [--path <path>]`

Parameters:

- `name` (required, typically `namespace.collection`)
- `path` (optional, workspace-relative)

Both tools return command output and command metadata.
