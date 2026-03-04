# Execution Environment Rules

- Use `version: 3` for modern execution-environment definitions.
- Always set `images.base_image.name`.
- Keep dependency lists explicit and minimal:
  - `dependencies.galaxy.collections`
  - `dependencies.system`
  - `dependencies.python`
- Prefer pinned collection and package versions for reproducibility.
- Avoid embedding secrets in the YAML.
- Validate the generated file against the schema before building.
- Build with `ansible-builder build --file <path> --context <context-dir> --tag <image-tag> -vvv`.
