# Upstream Tool Parity

This document tracks parity against the current upstream Ansible MCP tool surface.

## Upstream endpoints (current)

1. zen_of_ansible
2. ansible_content_best_practices
3. list_available_tools
4. ansible_lint
5. ade_environment_info
6. ade_setup_environment
7. adt_check_env
8. ansible_create_playbook
9. ansible_create_collection
10. define_and_build_execution_env
11. ansible_navigator

## Current status in this standalone server

- Implemented now:
  - zen_of_ansible
  - ansible_content_best_practices
  - list_available_tools
  - ansible_lint (mapped to `lint`)

- Planned for parity completion:
  - ade_environment_info
  - ade_setup_environment
  - adt_check_env
  - ansible_create_playbook
  - ansible_create_collection
  - define_and_build_execution_env
  - ansible_navigator

## Extensibility principle

Parity implementation is additive and plugin-driven:
- Keep each upstream endpoint in its own focused plugin or wrapper.
- Keep schema and output contracts stable.
- Add tests per endpoint (unit + integration where applicable).
- Avoid introducing non-upstream endpoints until parity is complete.
