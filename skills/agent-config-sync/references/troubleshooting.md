# 故障排查

- `CONFIG_FILE_NOT_FOUND`：切换到包含 `agent-config.yaml` 的目录，或传 `--config`。
- `CONFIG_YAML_INVALID`：修复 YAML 语法。
- `CONFIG_SCHEMA_INVALID`：按报错路径修复声明结构。
- `UNSUPPORTED_API_VERSION`：使用 `agent-config/v1`。
- `INVALID_CONDITION`：检查 `when` 条件和值域。
- `VARIABLE_NOT_FOUND`：定义变量或提供匹配 overlay / 环境变量。
- `VARIABLE_CYCLE`：打断变量循环引用。
- `MERGE_TYPE_CONFLICT`：不要在对象、数组之间隐式切换类型。
- `INVALID_ARRAY_OPERATION`：只对数组使用 `$append` / `$prepend`。
- `CLAUDE_FIELD_OUT_OF_SCOPE`：从 `settings.json` 声明中删除范围外字段。
- `TARGET_FILE_MODIFIED`：目标在上次应用后被修改；先审阅差异，明确同意覆盖后才用 `--force`。
- `TARGET_WRITE_FAILED` / `BACKUP_FAILED`：检查目标目录权限和磁盘空间。

