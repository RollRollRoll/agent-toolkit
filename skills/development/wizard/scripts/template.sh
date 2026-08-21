#!/usr/bin/env bash
#
# 向导（wizard）一步一步带着人走完一套手工流程。
# 由 wizard skill 生成。
#
# "STAGES" 标记以上的所有东西都是向导库：不要手改它。
# 每一步的 stage 写在标记以下。

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────
# 向导库：讨人喜欢、始终一致的 UX，每个向导里都一模一样。
# ──────────────────────────────────────────────────────────────────────────

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  BOLD=$(tput bold); DIM=$(tput dim); RESET=$(tput sgr0)
  BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1)
else
  BOLD=""; DIM=""; RESET=""; BLUE=""; GREEN=""; YELLOW=""; RED=""
fi

# 由作者在 stages 一节的开头设置。
TOTAL_STAGES=0

_STAGE_INDEX=0
ENV_FILE="${ENV_FILE:-.env}"
WRITTEN_ENV=()    # 本次运行写进 ENV_FILE 的 KEY
WRITTEN_SECRET=() # 本次运行设置的 secret 名字
SKIPPED=()        # 没能做成的事（比如 gh 不在）

# _clear 把终端擦干净，屏幕上只留当前这一步。
# 输出不是终端时它什么都不做，这样管道里的日志仍然可读。
_clear() {
  [[ -t 1 ]] || return 0
  if command -v tput >/dev/null 2>&1; then tput clear; else printf '\033[2J\033[3J\033[H'; fi
}

# banner "标题" 显示开场那一帧：这个向导是干什么的。
banner() {
  _clear
  printf '\n%s%s  %s%s\n' "$BOLD" "$BLUE" "$1" "$RESET"
  printf '%s  共 %s 个阶段%s\n\n' "$DIM" "$TOTAL_STAGES" "$RESET"
  printf '%s  浏览器由你来开；这个向导会准确告诉你该做什么，并把你复制回来的值\n' "$DIM"
  printf '  捕获下来。随时可以 Ctrl-C 停掉、以后再跑，\n'
  printf '  它记得已经存下来的值。%s\n' "$RESET"
  pause "准备好开始了吗？"
}

# stage "名字" 先清屏，再宣布一个阶段并显示进度。
# 清屏保证屏幕上只有当前这一步。
stage() {
  _clear
  _STAGE_INDEX=$((_STAGE_INDEX + 1))
  printf '\n%s%s▸ 阶段 %s/%s · %s%s\n' \
    "$BOLD" "$BLUE" "$_STAGE_INDEX" "$TOTAL_STAGES" "$1" "$RESET"
}

# say "..." 打印一行朴素的说明。
say()  { printf '  %s\n' "$1"; }
# step "..." 是人要在浏览器里做的一个动作，读起来像编了号。
step() { printf '  %s•%s %s\n' "$BLUE" "$RESET" "$1"; }
note() { printf '  %s%s%s\n' "$DIM" "$1" "$RESET"; }
warn() { printf '  %s⚠ %s%s\n' "$YELLOW" "$1" "$RESET"; }

# open_url URL 在人的浏览器里打开它，跨平台，含 WSL。
open_url() {
  local url="$1"
  printf '  %s↗ 正在打开%s %s\n' "$GREEN" "$RESET" "$url"
  { if   command -v wslview     >/dev/null 2>&1; then wslview "$url"
    elif command -v explorer.exe >/dev/null 2>&1; then explorer.exe "$url"
    elif command -v xdg-open    >/dev/null 2>&1; then xdg-open "$url"
    elif command -v open        >/dev/null 2>&1; then open "$url"
    else warn "没能打开浏览器，请手动访问：$url"; fi
  } >/dev/null 2>&1 || warn "没能打开浏览器，请手动访问：$url"
}

# pause "msg" 等着人确认他已经做完了手工的那部分。
pause() {
  printf '  %s%s%s ' "$DIM" "${1:-按回车继续}" "$RESET"
  read -r _ || true
}

# confirm "问题" 是一道 y/N 闸门；回答 yes 才返回成功。
confirm() {
  local reply=""
  printf '  %s? %s [y/N] ' "$YELLOW" "$1"
  read -r reply || true
  [[ "$reply" =~ ^[Yy] ]]
}

# _existing KEY：ENV_FILE 里 KEY 当前的值（如果有）。
_existing() {
  [[ -f "$ENV_FILE" ]] || return 1
  local line; line=$(grep -E "^${1}=" "$ENV_FILE" | tail -n1) || return 1
  printf '%s' "${line#*=}"
}

# ask KEY "提示" 把一个值读进 $KEY。重跑时把 .env 里已有的值作为默认值
# 给出来（回车就保留它）。输入可见（非密钥）。
ask() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[回车保留当前值]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -r input || true
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

# ask_secret KEY "提示" 和 ask 一样，但输入是隐藏的。
ask_secret() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[回车保留当前值]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -rs input || true
  printf '\n'
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

# write_env KEY VALUE 把 KEY=VALUE upsert 进 ENV_FILE（文件不存在就建，
# 已有的那一行会被替换）。幂等。
write_env() {
  local key="$1" value="$2" tmp
  touch "$ENV_FILE"
  tmp=$(mktemp)
  grep -vE "^${key}=" "$ENV_FILE" > "$tmp" || true
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  mv "$tmp" "$ENV_FILE"
  WRITTEN_ENV+=("$key")
  printf '  %s✓ 已写入%s %s → %s\n' "$GREEN" "$RESET" "$key" "$ENV_FILE"
}

# set_secret NAME VALUE 通过 gh 设置一个 GitHub Actions 仓库 secret。
# gh 不可用或没登录时，退化成一条警告（并记下来）。
set_secret() {
  local name="$1" value="$2"
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    if printf '%s' "$value" | gh secret set "$name" >/dev/null 2>&1; then
      WRITTEN_SECRET+=("$name")
      printf '  %s✓ 已设置%s GitHub secret %s\n' "$GREEN" "$RESET" "$name"
      return
    fi
  fi
  SKIPPED+=("GitHub secret $name（手动设置：gh secret set $name）")
  warn "跳过了 GitHub secret $name：gh 还没就绪；稍后自己设一下"
}

# set_var NAME VALUE 设置一个 GitHub Actions 仓库变量（非密钥）。
set_var() {
  local name="$1" value="$2"
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    if gh variable set "$name" --body "$value" >/dev/null 2>&1; then
      printf '  %s✓ 已设置%s GitHub 变量 %s\n' "$GREEN" "$RESET" "$name"
      return
    fi
  fi
  SKIPPED+=("GitHub 变量 $name")
  warn "跳过了 GitHub 变量 $name，gh 还没就绪；稍后自己设一下"
}

# finish 先清屏，再把配置好的一切做一份收尾总结。
finish() {
  _clear
  printf '\n%s%s  ✓ 配置完成%s\n' "$BOLD" "$GREEN" "$RESET"
  (( ${#WRITTEN_ENV[@]} ))    && note "写了 ${#WRITTEN_ENV[@]} 个值到 $ENV_FILE：${WRITTEN_ENV[*]}"
  (( ${#WRITTEN_SECRET[@]} )) && note "设了 ${#WRITTEN_SECRET[@]} 个 GitHub secret：${WRITTEN_SECRET[*]}"
  if (( ${#SKIPPED[@]} )); then
    printf '\n'; warn "还得你手动做的："
    for s in "${SKIPPED[@]}"; do note "  - $s"; done
  fi
  printf '\n'
}

# ──────────────────────────────────────────────────────────────────────────
# STAGES：这一节由你来写。人每走一步，一个 stage()。
# 把下面这个示例替换掉。把 TOTAL_STAGES 设成与你写的阶段数一致。
# ──────────────────────────────────────────────────────────────────────────

TOTAL_STAGES=1

banner "Stripe 配置"

# ── 示例阶段：替换成你真正的步骤 ───────────────────────────────────────────
stage "Stripe：API keys"
say "我们要去拿你的 Stripe 测试密钥，存起来给本地开发和 CI 用。"
open_url "https://dashboard.stripe.com/test/apikeys"
step "在 API keys 页面上，复制 Publishable key（以 pk_test_ 开头）。"
ask STRIPE_PUBLISHABLE_KEY "把 publishable key 粘过来："
step "在 Secret key 那一行点 'Reveal test key'，然后复制它。"
ask_secret STRIPE_SECRET_KEY "把 secret key 粘过来："
write_env STRIPE_PUBLISHABLE_KEY "$STRIPE_PUBLISHABLE_KEY"
write_env STRIPE_SECRET_KEY "$STRIPE_SECRET_KEY"
set_secret STRIPE_SECRET_KEY "$STRIPE_SECRET_KEY"   # CI 需要的是这一个
# ──────────────────────────────────────────────────────────────────────────

finish
