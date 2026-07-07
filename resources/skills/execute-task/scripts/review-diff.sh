#!/usr/bin/env bash
# 用途：execute-task 阶段 2 派 review 前生成本任务的 diff 文件。
# 用法：scripts/review-diff.sh <任务编号>
# 行为：在仓库根建 .execute-task/（含自忽略 .gitignore）、按轮次自动递增命名（R1/R2/R3…）、
#       跑 git diff（工作区未提交改动）写入文件，把写入路径打印到 stdout。
# 复审时重新运行同一命令即可生成新一轮文件，不要复用旧 diff。
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "用法: $(basename "$0") <任务编号>" >&2
  exit 1
fi
task_id="$1"

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "错误：当前目录不在 git 仓库内" >&2
  exit 1
}

work_dir="$repo_root/.execute-task"
mkdir -p "$work_dir"
[ -f "$work_dir/.gitignore" ] || printf '*\n' > "$work_dir/.gitignore"

round=1
while [ -f "$work_dir/task-${task_id}-review-R${round}.diff" ]; do
  round=$((round + 1))
done
out_file="$work_dir/task-${task_id}-review-R${round}.diff"

git -C "$repo_root" diff > "$out_file"

if [ ! -s "$out_file" ]; then
  echo "警告：生成的 diff 为空，确认执行 subagent 是否有实际改动" >&2
fi

echo "$out_file"
