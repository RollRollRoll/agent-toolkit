#!/usr/bin/env bash
# 用途：execute-task 阶段 2 每个任务开工前，确认真实工作区干净并记录任务起点 HEAD。
# 用法：scripts/task-baseline.sh <任务编号>
# 行为：拒绝任何非忽略的暂存、未暂存或未跟踪改动；将 HEAD 写入
#       .execute-task/task-N-base，供 review-diff.sh 校验任务期间没有提交漂移。
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "用法: $(basename "$0") <任务编号>" >&2
  exit 1
fi
task_id="$1"

case "$task_id" in
  ""|*[!A-Za-z0-9._-]*)
    echo "错误：任务编号只能包含字母、数字、点、下划线和连字符：$task_id" >&2
    exit 1
    ;;
esac

script_dir=$(cd "$(dirname "$0")" && pwd)
work_dir=$("$script_dir/workspace.sh")
repo_root=$(git rev-parse --show-toplevel)

head_commit=$(git -C "$repo_root" rev-parse --verify HEAD 2>/dev/null) || {
  echo "错误：当前仓库没有可用的 HEAD commit，无法记录任务基线" >&2
  exit 1
}

status=$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all)
if [ -n "$status" ]; then
  echo "错误：任务开工前工作区必须干净；请先处理以下非忽略改动：" >&2
  printf '%s\n' "$status" >&2
  exit 1
fi

base_file="$work_dir/task-${task_id}-base"
printf '%s\n' "$head_commit" > "$base_file"
echo "$base_file"
