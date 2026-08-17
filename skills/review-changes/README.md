# Review Changes

## 用途

**composable 层**的整体改动审查能力单元：把一段已完成的改动（默认 `BASE..HEAD` 整条开发线）
凝固成一份审查包一次读完，按 **correctness / readability / architecture / security / performance**
五轴加**测试质量**共六关逐项判定，输出带 `file:line` 的 **Critical / Important / Minor** 分级 findings。

只读不改：不动工作区、不动 git 状态、不修 findings——修复由调用方决定谁来做、修不修。

**测试质量是第六关，不是附加题**：红绿循环里没有 reviewer 审过测试本身，这里是唯一关口——
一批全绿的同义反复测试等于没有测试。

## 触发场景

- "审一遍这条分支再合 / review 这次改动 / 这批代码有没有问题"
- 由 **execute-task**（workflow 层）在阶段 3 整体验收时调用。
- 不适用：改动还没写完；只想跑测试；要的是动手修复而不是审查；评审需求或技术方案本身
  （那是 **write-spec / make-design**）。

## 调用契约

| 方向 | 内容 |
|---|---|
| 传入 | `BASE` 起点 commit（或已生成的审查包路径）、需求依据（可选）、执行期疑虑（可选）、回执落盘路径（可选） |
| 取回 | 分级 findings（带 `file:line`）+ 六关各一句判定 + 具体的"做得好的" |
| 不做 | 不改代码、不 commit、不动 git 状态、不做系统性覆盖核对回扫、不重做需求 / 技术方案 |

**独立性由调用方保证**：审的人不能是写的人。调用方参与过实现时，须派 fresh 上下文的 subagent
加载本 skill 并显式指定最强档；平台无此能力时记录降级原因，由调用方以 fresh 视角完整走一遍六关，
不删掉这道门。

## 使用方式

把本目录下的 `SKILL.md`、`references/` 和 `scripts/` 复制到目标平台的 skill 目录
（Claude Code：`.claude/skills/review-changes/`；Codex：`.agents/skills/review-changes/`）即可直接使用；
若 `scripts/` 下脚本丢失可执行权限，按所在环境的权限变更规则取得确认后，再补一次 `chmod +x scripts/*.sh`。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/axes.md`：六关逐项判据——每关看什么、什么算过、常见漏判。
- `scripts/review-package.sh`：拒绝 dirty 工作区并校验 `BASE` 是 `HEAD` 祖先后，生成
  `BASE..HEAD` 审查包（commit 清单 + 变更统计 + `-U10` 完整 diff），按轮次自动递增命名。
