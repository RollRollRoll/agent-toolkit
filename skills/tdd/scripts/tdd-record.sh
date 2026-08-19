#!/usr/bin/env bash
# 用途：tdd 闭环开工前，建好执行记录文件——证据必须落盘，上下文被压缩后只有它还在。
# 用法：scripts/tdd-record.sh <名称> [输出目录]
#       名称：记录标识（如 login-validation、task-2），生成 <名称>-record.md。
#       输出目录：可选。缺省用仓库根下自忽略的 .tdd/（不在 git 仓库则用当前目录）。
#                调用方要落进自己的工作目录时传第二个参数（execute 传 .execute/）。
# 行为：创建目录（点目录自动写自忽略 .gitignore）、按 references/record-format.md 的结构建文件，
#       **文件已存在则不覆盖**（支持中断后续做），最后把路径打印到 stdout。
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "用法: $(basename "$0") <名称> [输出目录]" >&2
  exit 1
fi
name="$1"

case "$name" in
  ""|*[!A-Za-z0-9._-]*)
    echo "错误：名称只能包含字母、数字、点、下划线和连字符：$name" >&2
    exit 1
    ;;
esac

if [ $# -eq 2 ]; then
  work_dir="$2"
else
  repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || repo_root="$PWD"
  work_dir="$repo_root/.tdd"
fi

mkdir -p "$work_dir"

case "$(basename "$work_dir")" in
  .*)
    [ -f "$work_dir/.gitignore" ] || printf '*\n' > "$work_dir/.gitignore"
    ;;
  *)
    echo "提示：$work_dir 不是自忽略的点目录，执行记录可能被提交进仓库" >&2
    ;;
esac

out_file="$work_dir/${name}-record.md"

if [ -f "$out_file" ]; then
  echo "$out_file"
  exit 0
fi

{
  printf '# TDD 执行记录：%s\n' "$name"
  cat <<'TEMPLATE'

> 边做边写：每转一次红或绿，立刻追加一次。事后凭印象补写的是回忆，不是证据。

## 需求依据

- seam：
- 验证方式：

## 行为 1：[一句话说清验的是什么行为]

- 红：`[测试命令]`
  ```
  [失败输出，保留关键几行]
  ```
  为何预期失败：[行为缺失在哪 —— 必须是行为缺失，不是语法 / import / 环境错]
- 绿：`[同一条测试命令]`
  ```
  [通过输出]
  ```

## 收尾验证

`[验证命令 + typecheck]`
```
[完整输出，含告警]
```

## 改动文件

- [路径]：[改了什么]

## 疑虑

- [看到但按规则没动的结构问题 —— 交回调用方]
TEMPLATE
} > "$out_file"

echo "$out_file"
