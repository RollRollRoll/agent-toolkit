# Merge rules

Overlays are applied in declaration order; a later matching overlay wins:

- Objects merge recursively.
- Scalars are replaced.
- Arrays are replaced as a whole by default.
- `{$append: [...]}` appends to the end of the existing array.
- `{$prepend: [...]}` adds to the start of the existing array.
- `{$delete: true}` deletes the field it is on.
- `null` is an ordinary value; it does not mean delete.

An array operation object may contain only one operator, and its target must be an array or not exist. An implicit type replacement between object and array raises `MERGE_TYPE_CONFLICT`, to avoid accidentally breaking the config structure.

