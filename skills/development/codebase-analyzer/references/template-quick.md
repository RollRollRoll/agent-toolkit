# Report template: quick overview tier

> This is the output skeleton for the **quick overview**. The goal is that the reader understands the project's purpose, basic structure, and one core flow in about 1 minute.
> Use it when the user says "take a quick look / brief intro / roughly what is it".
> For more detail, use [template-standard.md](template-standard.md) or [template-deep.md](template-deep.md) instead.
>
> **Requirements**:
> - Keep the whole report to **half a screen to one screen**; do not grow it into a long report.
> - Key conclusions still need a **source path**; do not guess from names / the README.
> - For anything you did not figure out, one line "未搞清楚 X" (X not figured out) is enough; no separate section.
>
> **How to fill this template** (same rules in all three templates):
> - Everything below the `---` line is the report skeleton. Headings, bold field labels, and table headers are **fixed Chinese strings**: copy them verbatim.
> - `{{...}}` placeholders describe what goes there, in English. Replace each one with Chinese content.
> - Blockquotes starting with `> Guidance:` are instructions for you. Do not copy them into the report.
> - English meaning of the fixed headings:
>
> | Heading | Meaning |
> |---|---|
> | `项目速览` | Project at a glance (report title) |
> | `一句话定义` | One-sentence definition |
> | `核心价值` | Core value |
> | `技术栈与形态` | Tech stack and form |
> | `目录地图（精简）` | Directory map (trimmed) |
> | `最核心的一条流程` | The single most central flow |
> | `想深入可以看` | Where to look to go deeper |

---

# 项目速览：{{project name}}

> **调研对象**：`{{absolute path or repository URL}}` ｜ **时间**：{{YYYY-MM-DD}}

## 一句话定义
{{what the project does and who it is for}}

## 核心价值
{{which pain point it solves}}

## 技术栈与形态
- **架构风格**：{{monolith / microservices / CLI / library / event-driven ...}}
- **主要技术栈**：{{language + key frameworks + database, all on one line}}
- **运行形态**：{{long-running server / one-shot CLI / scheduled job / SDK / frontend ...}}
- **代码规模感**：{{order of magnitude of lines / number of modules / monorepo or not}}

## 目录地图（精简）

```text
{{root directory}}/
├── {{dir1}}/   # {{responsibility}}
├── {{dir2}}/   # {{responsibility}}
└── …           # {{list only the 5-10 most important directories}}
```

## 最核心的一条流程
{{pick the flow users notice most and connect it in 3-5 sentences: where it is triggered → which key file it passes through (with path) → what it finally produces. No need to go hop by hop.}}

## 想深入可以看
- {{to understand the architecture → which directory / file to read}}
- {{to understand the core logic → read `path`}}
- 需要更完整的分析可切换到**标准调研**或**深度报告**档。
