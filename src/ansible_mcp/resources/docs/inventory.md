# inventory tools

## inventory_parse
Runs:
```bash
ansible-inventory -i <inventory_path> --list
```

## inventory_graph
Runs:
```bash
ansible-inventory -i <inventory_path> --graph
```

## Inputs
- `inventory_path` (required): inventory file or directory

## Notes
- Use `inventory_parse` for machine-readable content.
- Use `inventory_graph` for quick topology visualization.
