#!/usr/bin/env bash
# 用途：execute-task 阶段 2 派 review 前生成本任务的 diff 文件。
# 用法：scripts/review-diff.sh <任务编号>
# 行为：读取 task-baseline.sh 记录的任务起点，确认 HEAD 未漂移；按轮次自动递增命名
#       （R1/R2/R3…），生成相对 HEAD 的完整工作区 diff（暂存、未暂存、删除、未跟踪，
#       binary、-U10），不修改真实 index；把写入路径打印到 stdout。
# 复审时重新运行同一命令即可生成新一轮文件，不要复用旧 diff。
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

base_file="$work_dir/task-${task_id}-base"
if [ ! -f "$base_file" ]; then
  echo "错误：缺少任务基线：$base_file" >&2
  echo "请在派发执行 subagent 前先运行 task-baseline.sh $task_id" >&2
  exit 1
fi

base_commit=$(sed -n '1p' "$base_file")
git -C "$repo_root" rev-parse --verify --quiet "${base_commit}^{commit}" >/dev/null || {
  echo "错误：任务基线不是有效 commit：$base_commit" >&2
  exit 1
}
head_commit=$(git -C "$repo_root" rev-parse --verify HEAD)
if [ "$head_commit" != "$base_commit" ]; then
  echo "错误：任务期间 HEAD 已漂移，拒绝生成混合范围 diff" >&2
  echo "任务基线：$base_commit" >&2
  echo "当前 HEAD：$head_commit" >&2
  exit 1
fi

round=1
while [ -f "$work_dir/task-${task_id}-review-R${round}.diff" ]; do
  round=$((round + 1))
done
out_file="$work_dir/task-${task_id}-review-R${round}.diff"

git -C "$repo_root" diff --binary -U10 HEAD -- > "$out_file"

# git diff HEAD 已覆盖所有 tracked 变化；逐个补入未跟踪文件。--no-index 以 1 表示
# “存在差异”，不是失败；大于 1 才是真错误。整个过程只读，不触碰真实 index。
while IFS= read -r -d '' untracked_file; do
  diff_status=0
  git -C "$repo_root" diff --no-index --binary -U10 -- /dev/null "$untracked_file" >> "$out_file" || diff_status=$?
  if [ "$diff_status" -gt 1 ]; then
    echo "错误：无法生成未跟踪文件 diff：$untracked_file" >&2
    exit "$diff_status"
  fi
done < <(git -C "$repo_root" ls-files --others --exclude-standard -z)

if [ ! -s "$out_file" ]; then
  echo "警告：生成的 diff 为空，确认执行 subagent 是否有实际改动" >&2
fi

echo "$out_file"
