# execute-task 吸收 SDD 三脚本机制实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按已批准设计（`../specs/2026-07-08-absorb-sdd-scripts-design.md`）给 execute-task 补齐三个交接脚本与配套文档：简报抽取脚本化、任务级 diff 补 -U10、阶段 3 整体验收补 BASE..HEAD 审查包，`workspace.sh` 作为目录逻辑单一事实来源。

**Architecture:** 形态 A（上游 obra/superpowers 同构）——`scripts/workspace.sh` 负责 `.execute-task/` 目录的创建与定位，`task-brief.sh` / `review-diff.sh` / `acceptance-diff.sh` 经 `dirname "$0"` 调用它。文档层三份 references 同步机制措辞。验证全部在临时 git 仓库做脚本级验证（test-skill 全编排复测延后，不在本计划内）。

**Tech Stack:** bash（`set -euo pipefail`）、awk、git；无任何外部依赖。

## Global Constraints

- 所有脚本注释、报错信息、文档改动一律**中文**（遵循全局 CLAUDE.md）。
- 脚本风格与现有 `review-diff.sh` 一致：`#!/usr/bin/env bash` + `set -euo pipefail` + 头部中文用途注释；**stdout 只打印结果路径**，警告 / 错误一律走 stderr；新脚本创建后 `chmod +x`。
- 精准修改：文档只改本计划列出的段落，不顺手调整邻近措辞 / 格式。
- 两个工作目录严格分离：**验证**全部在临时仓库 `/tmp/claude-0/-root-workspace-agent-toolkit/979001b2-7228-46b6-b361-88fed667c0ac/scratchpad/sdd-verify`（下称 `$VERIFY`）里跑；**编辑与 commit** 全部在 `/root/workspace/agent-toolkit`（下称 `$REPO`）。每个命令块开头已写明 cwd。
- skill 脚本目录：`$REPO/resources/skills/execute-task/scripts`（下称 `$SCRIPTS`）。
- 本计划内的 commit 逐任务做（已获用户批准）；**不 push**——发布 push 由用户在收尾环节拍板。
- 环境变量约定（每个命令块可直接复制）：

```bash
export REPO=/root/workspace/agent-toolkit
export SCRIPTS=$REPO/resources/skills/execute-task/scripts
export VERIFY=/tmp/claude-0/-root-workspace-agent-toolkit/979001b2-7228-46b6-b361-88fed667c0ac/scratchpad/sdd-verify
```

---

### Task 1: workspace.sh — 交接目录的单一事实来源

**Files:**
- Create: `resources/skills/execute-task/scripts/workspace.sh`

**Interfaces:**
- Consumes: 无（只依赖 git 与 cwd 所在仓库）
- Produces: 无参数调用；stdout 打印 `<repo-root>/.execute-task` 绝对路径；保证该目录存在且含只有 `*` 的 `.gitignore`；非 git 仓库内报错 exit 1。Task 2/3/4 的脚本都通过 `"$(cd "$(dirname "$0")" && pwd)/workspace.sh"` 调用它。

- [ ] **Step 1: 建验证用临时仓库**

```bash
export VERIFY=/tmp/claude-0/-root-workspace-agent-toolkit/979001b2-7228-46b6-b361-88fed667c0ac/scratchpad/sdd-verify
rm -rf "$VERIFY" && mkdir -p "$VERIFY" && cd "$VERIFY"
git init -q && git commit -q --allow-empty -m "init"
```

Expected: 无输出，`$VERIFY` 成为空 git 仓库。

- [ ] **Step 2: 跑一次证明脚本还不存在（红）**

```bash
cd "$VERIFY" && bash "$SCRIPTS/workspace.sh"
```

Expected: `bash: .../workspace.sh: No such file or directory`，退出码非 0。

- [ ] **Step 3: 写 workspace.sh**

写入 `$SCRIPTS/workspace.sh`，内容全文：

```bash
#!/usr/bin/env bash
# 用途：解析并确保 execute-task 交接文件的工作目录存在，打印其绝对路径。
# 它是目录约定的单一事实来源：task-brief.sh / review-diff.sh / acceptance-diff.sh
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
```

然后 `chmod +x "$SCRIPTS/workspace.sh"`。

- [ ] **Step 4: 验证（绿）**

```bash
cd "$VERIFY"
"$SCRIPTS/workspace.sh"          # 期望输出：$VERIFY/.execute-task
cat .execute-task/.gitignore      # 期望输出：*
"$SCRIPTS/workspace.sh"          # 再跑幂等：输出同上，无报错
git status --porcelain            # 期望输出：空（.execute-task 被自忽略）
cd "$VERIFY/.." && "$SCRIPTS/workspace.sh"   # 非 git 目录
```

Expected: 前四条如注释；最后一条 stderr 输出 `错误：当前目录不在 git 仓库内`，退出码 1。

- [ ] **Step 5: Commit**

```bash
cd "$REPO"
git add resources/skills/execute-task/scripts/workspace.sh
git commit -m "feat(execute-task): 新增 workspace.sh——交接目录的单一事实来源"
```

---

### Task 2: review-diff.sh 改造 — -U10 + 调 workspace.sh

**Files:**
- Modify: `resources/skills/execute-task/scripts/review-diff.sh`

**Interfaces:**
- Consumes: Task 1 的 `workspace.sh`（同目录，`dirname "$0"` 定位）
- Produces: 接口**不变**——`review-diff.sh <任务编号>`，stdout 打印 `.execute-task/task-N-review-R<轮>.diff` 路径；diff 上下文从 -U3 变 **-U10**。

- [ ] **Step 1: 构造 U10 可检验 fixture 并证明现状不满足（红）**

```bash
cd "$VERIFY"
seq -f 'line-%g' 30 > file.txt && git add file.txt && git commit -qm "add file.txt"
sed -i 's/^line-15$/line-15-CHANGED/' file.txt
"$SCRIPTS/review-diff.sh" u3probe
grep -c '^ line-7$' .execute-task/task-u3probe-review-R1.diff
```

Expected: 脚本打印 diff 路径；`grep -c` 输出 `0` 退出码 1——改动在 line-15，距 8 行的 line-7 在 U3（±3 行）上下文外，证明现状纪律"diff 上下文行就是改动后的文件"立不住。

- [ ] **Step 2: 改造 review-diff.sh**

把 `$SCRIPTS/review-diff.sh` 整体改为（全文替换，保留可执行权限）：

```bash
#!/usr/bin/env bash
# 用途：execute-task 阶段 2 派 review 前生成本任务的 diff 文件。
# 用法：scripts/review-diff.sh <任务编号>
# 行为：经同目录 workspace.sh 取 .execute-task/（含自忽略 .gitignore）、按轮次自动递增命名
#       （R1/R2/R3…）、跑 git diff -U10（工作区未提交改动；扩展上下文让 review 不必另读改动文件）
#       写入文件，把写入路径打印到 stdout。
# 复审时重新运行同一命令即可生成新一轮文件，不要复用旧 diff。
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "用法: $(basename "$0") <任务编号>" >&2
  exit 1
fi
task_id="$1"

script_dir=$(cd "$(dirname "$0")" && pwd)
work_dir=$("$script_dir/workspace.sh")
repo_root=$(git rev-parse --show-toplevel)

round=1
while [ -f "$work_dir/task-${task_id}-review-R${round}.diff" ]; do
  round=$((round + 1))
done
out_file="$work_dir/task-${task_id}-review-R${round}.diff"

git -C "$repo_root" diff -U10 > "$out_file"

if [ ! -s "$out_file" ]; then
  echo "警告：生成的 diff 为空，确认执行 subagent 是否有实际改动" >&2
fi

echo "$out_file"
```

（相对原版的差异只有三处：头注释更新、目录逻辑改调 `workspace.sh`、`git diff` 加 `-U10`；轮次命名 / 空 diff 警告 / 单参数接口原样保留。）

- [ ] **Step 3: 验证（绿）**

```bash
cd "$VERIFY"
"$SCRIPTS/review-diff.sh" u10probe
grep -c '^ line-7$' .execute-task/task-u10probe-review-R1.diff    # 期望 1
grep -c '^ line-23$' .execute-task/task-u10probe-review-R1.diff   # 期望 1
"$SCRIPTS/review-diff.sh" u10probe                                # 期望打印 …-R2.diff（轮次递增不回归）
git checkout -- file.txt
"$SCRIPTS/review-diff.sh" cleanprobe
```

Expected: line-7 / line-23（距改动 8 行）都进了上下文，证明 -U10 生效；第二跑打印 `task-u10probe-review-R2.diff`；最后一跑 stderr 出现 `警告：生成的 diff 为空…`（空 diff 警告不回归），stdout 仍打印路径。

- [ ] **Step 4: Commit**

```bash
cd "$REPO"
git add resources/skills/execute-task/scripts/review-diff.sh
git commit -m "feat(execute-task): review-diff.sh 补 -U10 并改经 workspace.sh 取目录"
```

---

### Task 3: task-brief.sh — 简报抽取脚本化

**Files:**
- Create: `resources/skills/execute-task/scripts/task-brief.sh`

**Interfaces:**
- Consumes: Task 1 的 `workspace.sh`
- Produces: `task-brief.sh <tasks文件> <任务编号>`；stdout 打印 `.execute-task/task-N-brief.md` 路径；抽取 `### Task N:` 段（fence 内假标题不算；下一个 Task 标题或**非 Task 的一、二级标题**终止）；任务号不存在 exit 3、参数 / 文件错 exit 1。Task 5 的文档改动引用此接口。

- [ ] **Step 1: 写验证 fixture**

写入 `$VERIFY/tasks-fixture.md`，内容全文（覆盖：精确值保真、fence 假标题 + fence 内假章节、Task 1 vs Task 10 区分、尾部截断）：

````markdown
# 任务清单：示例主题

## 背景 / 范围
- 实现某份 design。

## 任务列表

### Task 1: 建立数据模型
- 切片：地基任务
- 涉及文件：src/models.py
- 依赖：none；可并行：否；高风险：否
- 验收标准：模型字段与 design 一致，精确值 max_retries=7
- 验证方式：`pytest tests/test_models.py`
- 覆盖：design 组件 A
- [ ] 完成

```python
### Task 99: 这是 code fence 里的假标题，不该被当成任务
## 假章节标题也不该切断抽取
def demo():
    pass
```

### Task 2: 实现接口
- 切片：切片一
- 依赖：Task 1；可并行：否；高风险：否
- 验收标准：接口签名 create_user(name: str) -> User
- 验证方式：`pytest tests/test_api.py`
- [ ] 完成

### Task 10: 收尾清理
- 切片：切片一
- 依赖：Task 2
- 验收标准：无死代码
- 验证方式：`pytest`
- [ ] 完成

## 依赖与并行视图
- 顺序：T1 → T2 → T10
- 尾部章节不该出现在任何任务简报里

## 覆盖核对表
| design / spec 条目 | 任务落点 |
|---|---|
| 组件 A | Task 1 |
````

- [ ] **Step 2: 跑一次证明脚本还不存在（红）**

```bash
cd "$VERIFY" && bash "$SCRIPTS/task-brief.sh" tasks-fixture.md 1
```

Expected: `No such file or directory`，退出码非 0。

- [ ] **Step 3: 写 task-brief.sh**

写入 `$SCRIPTS/task-brief.sh`，内容全文：

```bash
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
```

然后 `chmod +x "$SCRIPTS/task-brief.sh"`。

awk 四条规则解读（维护者视角）：① fence 栏杆行翻转 infence；② fence 外遇到任意 Task 标题行，按"是不是要找的那个 N"重设 intask（`([^0-9]|$)` 守卫防 Task 1 匹配 Task 10）；③ fence 外、在任务内、遇到**非 Task 的一/二级标题**（`^# ` / `^## `，任务标题固定三级不受影响）→ 终止，这是对上游的适配——否则最后一个任务会把「依赖与并行视图」等尾部章节全带上；④ intask 期间逐行打印（含任务内的 fence 代码块）。

- [ ] **Step 4: 验证（绿，覆盖六个点）**

```bash
cd "$VERIFY"
B1=$("$SCRIPTS/task-brief.sh" tasks-fixture.md 1) && echo "$B1"   # 期望 …/task-1-brief.md
grep -c 'max_retries=7' "$B1"        # 期望 1：精确值逐字保真
grep -c 'Task 99' "$B1"              # 期望 1：fence 假标题作为正文保留（fence 保护生效，未在 99 处切断）
grep -c '### Task 2' "$B1"           # 期望 0：在下一个 Task 标题正确终止
grep -c '收尾清理' "$B1"             # 期望 0：Task 1 没把 Task 10 段吞进来
B10=$("$SCRIPTS/task-brief.sh" tasks-fixture.md 10) && grep -c '依赖与并行视图' "$B10"   # 期望 0：尾部截断生效
grep -c '收尾清理' "$B10"            # 期望 1：Task 10 本体抽到了
"$SCRIPTS/task-brief.sh" tasks-fixture.md 3;  echo "exit=$?"      # 期望 stderr 报错、exit=3
"$SCRIPTS/task-brief.sh" tasks-fixture.md 99; echo "exit=$?"      # 期望 exit=3：fence 内假标题不算任务
"$SCRIPTS/task-brief.sh" no-such-file.md 1;   echo "exit=$?"      # 期望 stderr 报错、exit=1
```

Expected: 各行注释所示。注意 `grep -c` 无匹配时输出 0 且退出码 1，属预期，别当失败处理。

- [ ] **Step 5: Commit**

```bash
cd "$REPO"
git add resources/skills/execute-task/scripts/task-brief.sh
git commit -m "feat(execute-task): 新增 task-brief.sh——简报抽取脚本化防手抄失真"
```

---

### Task 4: acceptance-diff.sh — 阶段 3 整体验收审查包

**Files:**
- Create: `resources/skills/execute-task/scripts/acceptance-diff.sh`

**Interfaces:**
- Consumes: Task 1 的 `workspace.sh`
- Produces: `acceptance-diff.sh <BASE>`（BASE = 阶段 1 记入账本的起点 commit，HEAD 固定当前）；stdout 打印 `.execute-task/acceptance-R<轮>.diff` 路径；包内三段 = `git log --oneline` + `git diff --stat` + `git diff -U10`（均为 BASE..HEAD）；BASE 非法 exit 1；BASE..HEAD 无 commit 时 stderr 警告。Task 5 的文档改动引用此接口。

- [ ] **Step 1: 准备多 commit 场景并证明脚本不存在（红）**

```bash
cd "$VERIFY"
BASE=$(git rev-parse HEAD)
sed -i 's/^line-20$/line-20-changed/' file.txt && git commit -qam "change line-20"
echo "new content" > newfile.txt && git add newfile.txt && git commit -qm "add newfile"
bash "$SCRIPTS/acceptance-diff.sh" "$BASE"
```

Expected: 前面命令静默完成；最后一条 `No such file or directory`，退出码非 0。（`$BASE` 环境变量保持在当前 shell 里，供 Step 3 复用；若丢失可 `git rev-parse HEAD~2` 重取。）

- [ ] **Step 2: 写 acceptance-diff.sh**

写入 `$SCRIPTS/acceptance-diff.sh`，内容全文：

```bash
#!/usr/bin/env bash
# 用途：execute-task 阶段 3 整体验收前，生成整条开发线的审查包
#       （commit 清单 + 变更统计 + BASE..HEAD 完整 diff），供五轴 review 一次读完，不必自己爬库。
# 用法：scripts/acceptance-diff.sh <BASE>
#       BASE = 本次开发的起点 commit（阶段 1 记入账本的那个），HEAD 固定为当前。
# 行为：经同目录 workspace.sh 取 .execute-task/、按轮次自动递增命名（acceptance-R1.diff、R2…）、
#       写入三段内容，把写入路径打印到 stdout。阶段 3 fix 提交后重新运行即得含 fix 的新一轮包。
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "用法: $(basename "$0") <BASE起点commit>" >&2
  exit 1
fi
base="$1"

script_dir=$(cd "$(dirname "$0")" && pwd)
work_dir=$("$script_dir/workspace.sh")
repo_root=$(git rev-parse --show-toplevel)

git -C "$repo_root" rev-parse --verify --quiet "$base" >/dev/null || {
  echo "错误：BASE 不是有效的 commit / ref：$base" >&2
  exit 1
}

round=1
while [ -f "$work_dir/acceptance-R${round}.diff" ]; do
  round=$((round + 1))
done
out_file="$work_dir/acceptance-R${round}.diff"

{
  echo "# 整体验收审查包：${base}..HEAD"
  echo
  echo "## Commits"
  git -C "$repo_root" log --oneline "${base}..HEAD"
  echo
  echo "## Files changed"
  git -C "$repo_root" diff --stat "${base}..HEAD"
  echo
  echo "## Diff"
  git -C "$repo_root" diff -U10 "${base}..HEAD"
} > "$out_file"

commit_count=$(git -C "$repo_root" rev-list --count "${base}..HEAD")
if [ "$commit_count" -eq 0 ]; then
  echo "警告：${base}..HEAD 没有任何 commit，确认 BASE 是否正确" >&2
fi

echo "$out_file"
```

然后 `chmod +x "$SCRIPTS/acceptance-diff.sh"`。

- [ ] **Step 3: 验证（绿，覆盖四个点）**

```bash
cd "$VERIFY"
P1=$("$SCRIPTS/acceptance-diff.sh" "$BASE") && echo "$P1"          # 期望 …/acceptance-R1.diff
grep -c '^## Commits$\|^## Files changed$\|^## Diff$' "$P1"        # 期望 3：三段齐全
awk '/^## Commits$/{f=1;next} /^## Files changed$/{f=0} f&&NF' "$P1" | wc -l   # 期望 2：commit 清单两条
grep -c 'line-20-changed' "$P1"                                    # 期望不小于 1：diff 段真含改动内容
"$SCRIPTS/acceptance-diff.sh" "$BASE"                              # 期望打印 …/acceptance-R2.diff（轮次递增）
"$SCRIPTS/acceptance-diff.sh" not-a-ref; echo "exit=$?"            # 期望 stderr 报错、exit=1
"$SCRIPTS/acceptance-diff.sh" HEAD                                 # 期望 stderr 出现"没有任何 commit"警告，stdout 仍打印路径
```

Expected: 各行注释所示。

- [ ] **Step 4: Commit**

```bash
cd "$REPO"
git add resources/skills/execute-task/scripts/acceptance-diff.sh
git commit -m "feat(execute-task): 新增 acceptance-diff.sh——阶段 3 整体验收审查包（BASE..HEAD）"
```

---

### Task 5: 三份 references 文档同步机制措辞

**Files:**
- Modify: `resources/skills/execute-task/references/handoff-templates.md`
- Modify: `resources/skills/execute-task/references/orchestration.md`
- Modify: `resources/skills/execute-task/references/acceptance.md`

**Interfaces:**
- Consumes: Task 2/3/4 的脚本名与接口（`task-brief.sh <tasks文件> <任务编号>`、`review-diff.sh <任务编号>`、`acceptance-diff.sh <BASE>`、轮次命名、stdout 打印路径）
- Produces: 文档层的机制约定，供 skill 运行时的主 agent 遵循；无代码接口。

- [ ] **Step 1: handoff-templates.md 第〇节——简报步骤脚本化**

第〇节步骤 1、2 整体替换。old：

```markdown
1. 建临时工作目录 `.execute-task/`（仓库根下，内放一个只含 `*` 的 `.gitignore`，不提交）。
2. **任务简报** `[BRIEF_FILE]` = `.execute-task/task-N-brief.md`：从 tasks.md 摘出该任务全文
   （验收标准、验证方式、涉及文件）+ 相关 design/spec 片段。
```

new：

```markdown
1. 临时工作目录 `.execute-task/`（仓库根下，含自忽略 `.gitignore`，不提交）由各脚本经
   `scripts/workspace.sh` 自动创建，不必手建。
2. **任务简报** `[BRIEF_FILE]`：运行本 skill 目录下的 `scripts/task-brief.sh <tasks文件> <任务编号>`——
   它机械抽取该任务全文（验收标准、验证方式、涉及文件，精确值逐字保真）写入
   `.execute-task/task-N-brief.md` 并打印路径，任务号不存在会报错；**不要手抄任务正文**。
   然后主 agent 把相关 design/spec 片段**追加**到同一文件（这半截需要判断力，脚本管不了）。
```

- [ ] **Step 2: handoff-templates.md 第〇节步骤 4——diff 描述补 -U10**

old（步骤 4 内一句）：

```markdown
   它会建好 `.execute-task/`（含自忽略 `.gitignore`）、按轮次自动递增命名（R1/R2/R3…）、跑 `git diff` 写入文件，
```

new：

```markdown
   它会建好 `.execute-task/`（含自忽略 `.gitignore`）、按轮次自动递增命名（R1/R2/R3…）、跑 `git diff -U10`
   （扩展上下文，review 不必另读改动文件）写入文件，
```

- [ ] **Step 3: handoff-templates.md 新增第四节模板，原第四节顺延为第五节**

把现有标题 `## 四 · 派发前主 agent 自查` 改为 `## 五 · 派发前主 agent 自查`，并在其前插入新第四节：

````markdown
## 四 · 整体验收 review 派发模板（阶段 3）

先跑 `scripts/acceptance-diff.sh <起点commit>`（起点 = 阶段 1 记入账本的起点 commit）生成整体审查包，
拿打印路径填 `[PACKAGE_FILE]`。五轴定义与覆盖回扫住在 acceptance.md，此处不重复。

```text
你来做整体验收 review：全部任务已完成，对整条开发线做五轴审查。
这次派发用最强档模型（见 model-selection.md），是全链路唯一的架构级判断点。

## 审查范围

整体审查包：[PACKAGE_FILE]（commit 清单 + 变更统计 + BASE..HEAD 完整 diff，-U10 上下文）
读一次即可——上下文行就是改动后的文件。只有为核实一个能点名的具体风险才看包外代码，
并在回执里写明查了什么。你只读不改：不动工作区、不动 git 状态。

## 审什么

按 acceptance.md「整体五轴 review」：correctness / readability / architecture / security / performance。
参考输入：tasks 文件 [TASKS_FILE]、design/spec [DESIGN_SPEC_PATHS]。

## 回执格式

同任务级 review：每条 finding 带 file:line、按 Critical / Important / Minor 分级、
先说做得好的再列问题，最后按五轴各给一句判定。
```

> 阶段 3 审出的 Critical / Important：fix 派发**复用第三节任务级 fix 模板**，「任务简报」位换成
> design/spec 路径、边界从"单任务"换成"本次开发范围"；fix 后主 agent **先 commit 再复审**——
> 重跑 `scripts/acceptance-diff.sh <起点>` 生成新一轮包（机制与理由见 acceptance.md）。
````

- [ ] **Step 4: handoff-templates.md 自查清单补两条**

在（顺延后的）第五节自查清单末尾追加：

```markdown
- 简报是 `task-brief.sh` 生成的基底 + 追加片段？没有手抄任务正文？
- 阶段 3 派发传了 `acceptance-diff.sh` 生成的整体包路径？fix 后是 commit 过再重新生成的新包？
```

- [ ] **Step 5: orchestration.md 第四节——简报 bullet 与 diff bullet**

简报 bullet，old：

```markdown
  - **任务简报** `task-N-brief.md`：主 agent 从 tasks.md 摘出该任务全文（验收标准、验证方式、涉及文件）
    + 相关 design/spec 片段。它是需求的**唯一来源**——精确值（数字、签名、测试用例）只出现在这里，不重复粘进 prompt；
```

new：

```markdown
  - **任务简报** `task-N-brief.md`：运行本 skill 目录下的 `scripts/task-brief.sh <tasks文件> <任务编号>`
    机械抽取该任务全文（**不要手抄**，精确值逐字保真），再由主 agent 追加相关 design/spec 片段。
    它是需求的**唯一来源**——精确值（数字、签名、测试用例）只出现在这里，不重复粘进 prompt；
```

diff bullet，old（其中一句）：

```markdown
    （执行 subagent 不 commit，工作区 diff 即该任务改动；脚本自动按轮次命名并打印写入路径，不必人工记编号；
```

new：

```markdown
    （执行 subagent 不 commit，工作区 diff 即该任务改动；脚本以 -U10 扩展上下文、自动按轮次命名并打印写入路径，不必人工记编号；
```

- [ ] **Step 6: orchestration.md 第五节——ledger 记起点 commit**

old：

```markdown
- **ledger**：记已完成任务 + 对应 commit（便于追溯）。
```

new：

```markdown
- **ledger**：开工时先记**起点 commit**（`git rev-parse HEAD`——阶段 3 生成整体审查包的 BASE）；
  执行中记已完成任务 + 对应 commit（便于追溯）。
```

同时把收尾自检中 handoff 一条，old：

```markdown
- handoff 走的是文件（简报 / 报告 / diff 传路径）而非粘贴正文？执行回执带了状态（DONE / BLOCKED…）且按状态处理了？
```

new：

```markdown
- handoff 走的是文件（简报 / 报告 / diff 传路径）而非粘贴正文？简报是 `task-brief.sh` 抽取的（没手抄）？
  执行回执带了状态（DONE / BLOCKED…）且按状态处理了？
```

- [ ] **Step 7: acceptance.md 第二节——输入准备与 fix 循环**

在第二节标题下、"全部任务完成后…"段落前插入输入准备段，并在五轴列表后补 fix 循环段。插入段一（紧跟 `## 二 · 整体五轴 review（闸门二）` 标题后）：

```markdown
**输入准备**：派发前运行本 skill 目录下的 `scripts/acceptance-diff.sh <起点commit>`（起点 = 阶段 1
记入账本的起点 commit）——生成整体审查包（commit 清单 + 变更统计 + BASE..HEAD 完整 diff，-U10）
并打印路径，派发时传包路径（照抄 handoff-templates.md 第四节模板），不让 review subagent 自己爬库推导改动。
```

插入段二（五轴列表之后、`## 三 · 覆盖核对回扫` 之前）：

```markdown
**阶段 3 的 fix 循环（commit-then-review）**：审出的 Critical / Important 派独立 fix subagent 修复后，
主 agent **先 commit 再复审**——重跑 `scripts/acceptance-diff.sh <起点>`（轮次递增，HEAD 已前进，
新包已含 fix），复审读一个新包。与任务级"不过不 commit"**有意不同**：任务级的 commit 是闸门记号；
阶段 3 面对的本来就是已 commit 的分支，闸门记号是"整体验收通过"状态本身，fix commit 只是普通代码演进。
```

- [ ] **Step 8: acceptance.md 收尾自检补一条**

在收尾自检清单"整体过了五轴 review…"一条之后插入：

```markdown
- 整体 review 拿到的是 `acceptance-diff.sh` 生成的审查包（而非让它自己爬库）？fix 后复审用的是 commit 过再重新生成的新包？
```

- [ ] **Step 9: 三文档交叉一致性核对**

```bash
cd "$REPO"
grep -n 'task-brief.sh\|acceptance-diff.sh\|workspace.sh\|review-diff.sh' \
  resources/skills/execute-task/references/handoff-templates.md \
  resources/skills/execute-task/references/orchestration.md \
  resources/skills/execute-task/references/acceptance.md
```

Expected: 所有引用的脚本名、参数形态（`<tasks文件> <任务编号>` / `<任务编号>` / `<起点commit>`）与 Task 2/3/4 实现一致；handoff-templates 的节号引用（acceptance.md 引"第四节模板"）成立。

- [ ] **Step 10: Commit**

```bash
cd "$REPO"
git add resources/skills/execute-task/references/
git commit -m "docs(execute-task): references 三件套同步脚本化 handoff——简报抽取、-U10、阶段 3 审查包与 commit-then-review"
```

---

### Task 6: README + metadata 同步 + validate 收尾

**Files:**
- Modify: `resources/skills/execute-task/README.md`
- Modify: `resources/skills/execute-task/metadata.yaml`

**Interfaces:**
- Consumes: Task 1-4 的脚本清单（目录说明要列全）
- Produces: 无；发布性收尾。

- [ ] **Step 1: README 使用方式——chmod 句改通配**

old：

```markdown
若 `scripts/review-diff.sh` 丢失可执行权限，补一次 `chmod +x scripts/review-diff.sh`。
```

new：

```markdown
若 `scripts/` 下脚本丢失可执行权限，补一次 `chmod +x scripts/*.sh`。
```

- [ ] **Step 2: README 目录说明——补三个脚本**

old：

```markdown
- `scripts/review-diff.sh`：生成派 review 前的任务 diff 文件，自动按轮次命名并打印写入路径。
```

new：

```markdown
- `scripts/workspace.sh`：交接目录 `.execute-task/` 的单一事实来源（建目录 + 自忽略 `.gitignore`，打印路径），其余脚本经它取目录。
- `scripts/task-brief.sh`：从 tasks 文档机械抽取单个任务全文生成简报基底，防手抄失真；design/spec 片段由主 agent 追加。
- `scripts/review-diff.sh`：生成派 review 前的任务 diff 文件（-U10 扩展上下文），自动按轮次命名并打印写入路径。
- `scripts/acceptance-diff.sh`：生成阶段 3 整体验收审查包（BASE..HEAD 的 commit 清单 + 变更统计 + 完整 diff）。
```

- [ ] **Step 3: metadata.yaml 同步维护日期**

old：`updated_at: 2026-07-07` → new：`updated_at: 2026-07-08`。

- [ ] **Step 4: validate 校验**

```bash
cd "$REPO" && claude plugin validate . --strict
```

Expected: 校验通过（无 error；同 825b826 先例，内容修改不递增插件版本）。

- [ ] **Step 5: 清理验证用临时仓库**

```bash
rm -rf "$VERIFY"
```

- [ ] **Step 6: Commit**

```bash
cd "$REPO"
git add resources/skills/execute-task/README.md resources/skills/execute-task/metadata.yaml
git commit -m "docs(execute-task): README 补三脚本说明，metadata 同步维护日期"
```

---

## 计划外（显式延后，见设计文档「延后项」）

- **test-skill 全编排复测**：验证主 agent 真的改用脚本生成简报而非惯性手抄（momentum 类失败单发子代理测不出）。作为独立后续任务另行安排，不属于本计划。
