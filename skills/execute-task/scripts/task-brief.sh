#!/usr/bin/env bash
# 用途：execute-task 派发执行前，从 tasks 文档机械抽取一个任务的全文生成简报基底——
#       精确值（数字、签名、测试用例）逐字保真，不经主 agent 手抄；
#       相关 design/spec 片段由主 agent 随后追加到同一文件。
# 用法：scripts/task-brief.sh <tasks文件> <任务编号>
# 行为：抽取 `### Task N:` 标题段（code fence 内的假标题不算；遇到下一个 Task 标题、
#       或非 Task 的一/二级标题即终止），写入 .execute-task/task-N-brief.md，
#       把写入路径打印到 stdout；任务号不存在则报错退出（exit 3）。
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "用法: $(basename "$0") <tasks文件> <任务编号>" >&2
  exit 1
fi
tasks_file="$1"
task_id="$2"

[ -f "$tasks_file" ] || {
  echo "错误：tasks 文件不存在：$tasks_file" >&2
  exit 1
}

script_dir=$(cd "$(dirname "$0")" && pwd)
work_dir=$("$script_dir/workspace.sh")
out_file="$work_dir/task-${task_id}-brief.md"

awk -v n="$task_id" '
  /^```/ { infence = !infence }
  !infence && /^#+[ \t]+Task[ \t]+[0-9]+/ {
    intask = ($0 ~ ("^#+[ \t]+Task[ \t]+" n "([^0-9]|$)"))
  }
  !infence && intask && /^##?[ \t]/ && $0 !~ /^#+[ \t]+Task[ \t]+[0-9]+/ { intask = 0 }
  intask { print }
' "$tasks_file" > "$out_file"

if [ ! -s "$out_file" ]; then
  echo "错误：在 $tasks_file 中找不到 Task ${task_id}（无匹配「Task ${task_id}」的标题）" >&2
  exit 3
fi

echo "$out_file"
