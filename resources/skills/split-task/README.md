# Split Task

## 用途

把一份**已确认的技术设计**（理想情况下来自 make-design），在动手编码前拆成一份
**可被 review、每个任务都能独立验收**的开发任务清单：按垂直切片切任务、
用拆分探针逐项扫易漏维度（迁移 / 测试 / 配置 / 回滚 / 可观测）防漏，
理顺依赖与并行、高风险前置，并逐条核对 design 组件与 spec 的 MUST / MUST NOT 都有任务落点
（不落空、不镀金），经用户 review 才放行进入编码。

它填补"技术方案定了"和"开始编码"之间的空档：止步于任务拆分层，
**不下沉到逐行实现代码 / 含代码施工单**（那是下游 execute-task 的事）。

## 触发场景

- "design 定了，把它拆成开发任务 / 帮我列实现任务清单"
- "把技术方案落地成可执行的 tasks"
- "这个功能怎么拆任务、按什么顺序做"
- 手上有 make-design 的技术设计，要继续往下拆任务。
- 不适用：技术方案还没定（先 make-design）；行为没钉死（先 write-spec）；想法还模糊（先 refine-idea）；
  要逐行实现代码 / 含代码施工单（那是下游 execute-task）；已在写代码 / 调 bug / 评审。

## 使用方式

将本目录下的 `SKILL.md` 和 `references/` 复制到目标平台的 skill 目录
（如 Claude Code 的 `.claude/skills/split-task/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/task-template.md`：任务清单落盘模板（含 greenfield 全量与 brownfield delta）。
- `references/split-probes.md`：拆分探针清单（11 个易漏任务维度），含每个维度问什么、怎么判级。
- `references/slicing-method.md`：切片与定序方法——垂直切片、任务分级、依赖与并行、高风险前置、覆盖核对。
- `docs/`：开发过程中的设计文档。
