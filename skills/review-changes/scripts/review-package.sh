#!/usr/bin/env bash
# 用途：review-changes 审查前，把 BASE..HEAD 凝固成一份审查包
#       （commit 清单 + 变更统计 + 完整 diff），供审查方一次读完，不必自己爬库。
# 用法：scripts/review-package.sh <BASE> [输出目录]
#       BASE：本段改动的起点 commit，HEAD 固定为当前。
#       输出目录：可选。缺省用仓库根下自忽略的 .review-changes/；
#                调用方要落进自己的工作目录时传第二个参数（execute 传 .execute/）。
# 行为：先拒绝任何非忽略的工作区改动、校验 BASE 是 HEAD 祖先，再按轮次自动递增命名
#       （review-R1.diff、R2…）写入三段内容，把路径打印到 stdout。
#       修复提交后重新运行即得含修复的新一轮包。
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "用法: $(basename "$0") <BASE起点commit> [输出目录]" >&2
  exit 1
fi
base="$1"

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "错误：当前目录不在 git 仓库内" >&2
  exit 1
}

if [ $# -eq 2 ]; then
  work_dir="$2"
else
  work_dir="$repo_root/.review-changes"
fi

base_commit=$(git -C "$repo_root" rev-parse --verify --quiet "${base}^{commit}") || {
  echo "错误：BASE 不是有效的 commit / ref：$base" >&2
  exit 1
}

head_commit=$(git -C "$repo_root" rev-parse --verify HEAD)
git -C "$repo_root" merge-base --is-ancestor "$base_commit" "$head_commit" || {
  echo "错误：BASE 不是当前 HEAD 的祖先，拒绝生成含义不明的审查范围" >&2
  echo "BASE：$base_commit" >&2
  echo "HEAD：$head_commit" >&2
  exit 1
}

status=$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all)
if [ -n "$status" ]; then
  echo "错误：生成审查包前工作区必须干净；以下改动不会进入 ${base_commit}..HEAD：" >&2
  printf '%s\n' "$status" >&2
  exit 1
fi

mkdir -p "$work_dir"
case "$(basename "$work_dir")" in
  .*)
    [ -f "$work_dir/.gitignore" ] || printf '*\n' > "$work_dir/.gitignore"
    ;;
  *)
    echo "提示：$work_dir 不是自忽略的点目录，审查包可能被提交进仓库" >&2
    ;;
esac

round=1
while [ -f "$work_dir/review-R${round}.diff" ]; do
  round=$((round + 1))
done
out_file="$work_dir/review-R${round}.diff"

{
  echo "# 审查包：${base_commit}..HEAD"
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
