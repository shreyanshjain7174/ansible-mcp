# Execution Environment Tool

## `define_and_build_execution_env`

Two-step flow compatible with upstream semantics:

1. **Prompt mode**: call without `generatedYaml` to receive a scaffold prompt.
2. **Write mode**: call again with `generatedYaml` to write `execution-environment.yml`.

Inputs:

- `baseImage` (required)
- `tag` (required)
- `destinationPath` (optional)
- `collections` (optional)
- `systemPackages` (optional)
- `pythonPackages` (optional)
- `generatedYaml` (optional; required for write mode)

Output includes:

- generated file path
- suggested `ansible-builder build ...` command
- lightweight validation warnings (if detected)

Related MCP resources:

- `schema://execution-environment`
- `sample://execution-environment`
- `rules://execution-environment`
