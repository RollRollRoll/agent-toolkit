#!/usr/bin/env bash
# 用途：解析并确保 execute-task 交接文件的工作目录存在，打印其绝对路径。
# 它是目录约定的单一事实来源：task-brief.sh / task-baseline.sh / review-diff.sh / acceptance-diff.sh
# 都经它取目录，防三处约定漂移。
# 目录放工作树内（而非 .git/ 下）是因为 subagent 通常写不了 .git/；
# 自忽略 .gitignore 保证它不进 git status、不被提交。
# 用法：scripts/workspace.sh
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "错误：当前目录不在 git 仓库内" >&2
  exit 1
}

work_dir="$repo_root/.execute-task"
mkdir -p "$work_dir"
[ -f "$work_dir/.gitignore" ] || printf '*\n' > "$work_dir/.gitignore"
echo "$work_dir"
