# playbook tools

## playbook_syntax_check
Runs:
```bash
ansible-playbook <playbook_path> [ -i <inventory_path> ] --syntax-check
```

## playbook_run
Runs:
```bash
ansible-playbook <playbook_path> [ -i <inventory_path> ] [--check] [--limit <pattern>]
```

## Inputs
- `playbook_path` (required): path to playbook YAML
- `inventory_path` (optional): inventory path
- `check` (optional boolean): check mode (dry-run)
- `limit` (optional string): host limit pattern

## Response
Structured result with:
- `status`
- `command`
- `exit_code`
- `stdout`
- `stderr`
