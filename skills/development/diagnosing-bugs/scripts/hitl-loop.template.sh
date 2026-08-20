#!/usr/bin/env bash
# 用途：diagnosing-bugs 阶段 1 的最后手段——需要人来点的复现回路。
#       复制这个文件，改下面的步骤，然后运行它。
#       agent 负责跑脚本，用户在自己的终端里跟着提示走。
# 用法：bash hitl-loop.template.sh
#
# 两个 helper：
#   step "<指令>"              → 显示指令，等用户回车
#   capture VAR "<问题>"       → 显示问题，把用户的回答读进 VAR
#
# 结尾会把捕获到的值按 KEY=VALUE 打印出来，供 agent 解析。
#
# capture 会把值回显到终端，agent 从那里读到它——所以用 capture 收集观察结果，
# 把登录之类的动作留给 step。

set -euo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p "    [做完按回车] " _
}

capture() {
  local var="$1" question="$2" answer
  printf '\n>>> %s\n' "$question"
  read -r -p "    > " answer
  printf -v "$var" '%s' "$answer"
}

# --- 从这里开始改 -------------------------------------------------------

step "打开 http://localhost:3000 并登录。"

capture ERRORED "点一下「导出」按钮。报错了吗？(y/n)"

capture ERROR_MSG "把错误信息贴过来（没有就写 none）："

# --- 改到这里为止 -------------------------------------------------------

printf '\n--- 捕获到的值 ---\n'
printf 'ERRORED=%s\n' "$ERRORED"
printf 'ERROR_MSG=%s\n' "$ERROR_MSG"
