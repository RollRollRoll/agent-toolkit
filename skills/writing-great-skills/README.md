# Writing Great Skills

## 用途

提供一套编写和审查 Skill 的参考框架，以执行过程的可预测性为根原则，系统处理调用方式、描述触发、信息层级、渐进式披露、拆分、引导词、剪枝与常见失败模式。

## 触发场景

- 用户显式要求审查某个 Skill 为什么触发不稳定或执行不一致。
- 用户希望精简 Skill、调整引用层级或判断是否应该拆分。
- 用户要设计模型调用型与用户调用型 Skill 的边界。
- 不适用：自动创建 Skill 脚手架、测试业务代码或在用户未显式选择时自行介入。

## 调用边界

本 Skill 只供人类显式调用。Claude Code 使用 `disable-model-invocation: true`，Codex 使用 `policy.allow_implicit_invocation: false`，避免它的长篇参考内容成为常驻上下文负载。

## 使用方式

将本目录复制到目标平台的 skill 目录（Claude Code：`.claude/skills/writing-great-skills/`；Codex：`.agents/skills/writing-great-skills/`）即可使用。

## 目录说明

- `SKILL.md`：核心原则和审查框架。
- `references/glossary.md`：完整术语定义与失败模式。
- `agents/openai.yaml`：Codex 展示信息和显式调用策略。
- `LICENSE.upstream`：上游 MIT 许可证。

## 参考来源

设计改编自 [mattpocock/skills 的 `writing-great-skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-great-skills)，并按本仓库的中文 Skill 结构重新组织。
