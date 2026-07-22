#!/usr/bin/env bash
# 用途：execute-task 阶段 3 整体验收前，生成整条开发线的审查包
#       （commit 清单 + 变更统计 + BASE..HEAD 完整 diff），供五轴 review 一次读完，不必自己爬库。
# 用法：scripts/acceptance-diff.sh <BASE>
#       BASE = 本次开发的起点 commit（阶段 1 记入账本的那个），HEAD 固定为当前。
# 行为：先拒绝任何非忽略的工作区改动并校验 BASE 是 HEAD 祖先，再经同目录 workspace.sh
#       取 .execute-task/、按轮次自动递增命名（acceptance-R1.diff、R2…）、写入三段内容，
#       把写入路径打印到 stdout。阶段 3 fix 提交后重新运行即得含 fix 的新一轮包。
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "用法: $(basename "$0") <BASE起点commit>" >&2
  exit 1
fi
base="$1"

script_dir=$(cd "$(dirname "$0")" && pwd)
work_dir=$("$script_dir/workspace.sh")
repo_root=$(git rev-parse --show-toplevel)

base_commit=$(git -C "$repo_root" rev-parse --verify --quiet "${base}^{commit}") || {
  echo "错误：BASE 不是有效的 commit / ref：$base" >&2
  exit 1
}

head_commit=$(git -C "$repo_root" rev-parse --verify HEAD)
git -C "$repo_root" merge-base --is-ancestor "$base_commit" "$head_commit" || {
  echo "错误：BASE 不是当前 HEAD 的祖先，拒绝生成含义不明的验收范围" >&2
  echo "BASE：$base_commit" >&2
  echo "HEAD：$head_commit" >&2
  exit 1
}

status=$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all)
if [ -n "$status" ]; then
  echo "错误：整体验收前工作区必须干净；以下改动不会进入 ${base_commit}..HEAD：" >&2
  printf '%s\n' "$status" >&2
  exit 1
fi

round=1
while [ -f "$work_dir/acceptance-R${round}.diff" ]; do
  round=$((round + 1))
done
out_file="$work_dir/acceptance-R${round}.diff"

{
  echo "# 整体验收审查包：${base_commit}..HEAD"
  echo
  echo "## Commits"
  git -C "$repo_root" log --oneline "${base_commit}..HEAD"
  echo
  echo "## Files changed"
  git -C "$repo_root" diff --stat "${base_commit}..HEAD"
  echo
  echo "## Diff"
  git -C "$repo_root" diff --binary -U10 "${base_commit}..HEAD"
} > "$out_file"

commit_count=$(git -C "$repo_root" rev-list --count "${base_commit}..HEAD")
if [ "$commit_count" -eq 0 ]; then
  echo "警告：${base_commit}..HEAD 没有任何 commit，确认 BASE 是否正确" >&2
fi

echo "$out_file"
