# Navigator Tool

## `ansible_navigator`

Supports two operation modes:

- **Information mode**: call with `{}` to get usage guidance.
- **Execution mode**: provide `userMessage` or `filePath`.

Parameters:

- `userMessage` (required for typical execution mode)
- `filePath` (optional direct playbook path)
- `mode` (`stdout` or `interactive`, default `stdout`)
- `environment` (`auto`, `system`, `venv`, or specific env name/path)
- `disableExecutionEnvironment` (default `false`)

Behavior:

- resolves playbook path safely within workspace
- finds ansible-navigator based on requested environment
- runs `ansible-navigator run ...`
- retries with `--ee false` for container-engine related failures when appropriate
