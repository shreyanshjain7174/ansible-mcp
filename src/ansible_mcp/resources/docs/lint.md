# lint tool

## Purpose
Run `ansible-lint` against a target file or directory and return structured stdout/stderr/exit code.

## Inputs
- `path` (string, default `.`): file or directory to lint
- `config` (optional string): ansible-lint config path
- `tags` (optional string[]): ansible-lint tags to apply

## Example
```json
{
  "path": "playbooks/site.yml",
  "tags": ["yaml", "formatting"]
}
```

## Notes
- Returns `status=success` when exit code is `0`, otherwise `failed`.
- If `ansible-lint` is not installed, stderr will include `Command not found`.
