# Existing system

The existing-system branch of [`ontology-decomposition`](../SKILL.md). It runs two paths and compares them:

```text
目标本体模型 − 现有系统语义模型 = 产品架构差异
```

- **Top-down** builds the **target ontology** from business goals and real scenarios: steps 1-6 of `SKILL.md`.
- **Bottom-up** builds the **existing semantic model** from what the system already encodes.

## Order

1. Run steps 1-6 from business sources only. Open pages, schema, API definitions, and code after step 6 is written to disk: a target ontology shaped by today's modules reproduces them and shows no gap.
2. Run the bottom-up extraction below.
3. Run step 7, filling the capability matrix from the extraction: each cell names the existing function, service, API, or table with its evidence, and 现状 is 已有, 部分, or 缺口.
4. Run step 8.
5. Run the gap analysis below.

When the system itself is the only business source available, ask the user for the goals and scenarios. If they have none to give, deliver the existing semantic model alone and say in the report that no gap can be computed without a target.

## Bottom-up extraction

Read each source for the semantics it implies:

| Source | What it reveals |
|---|---|
| Pages, menus, forms | the objects users operate, the actions offered, rules enforced only in the UI |
| Database schema, migrations | objects and properties, relations (foreign keys, join tables), states (status columns, enums), history tables |
| API definitions, routes | actions (commands), queries, the objects each endpoint exposes |
| Business logic | hidden rules (validators, guards, permission checks), state transitions, scheduled jobs, compensation code |
| Messages, webhooks, audit logs | events |

Record every extracted element with its evidence as `path:line`, under the name the system uses. Keep that name even where it differs from the target term: the mismatch is a finding.

Where a subagent tool exists, dispatch one extraction per source kind in parallel, each with a fresh context window. Give each the scope, the table row it owns, and the seven categories from step 3; keep the target ontology out of the brief, so the extraction reports what the system says.

Done when every table, endpoint, page, and status enum in scope is either mapped to an extracted element or listed as skipped with its reason.

## Gap analysis

Align the two models element by element and write `07-gap-analysis.md`. Classify every difference:

| Kind | What it looks like |
|---|---|
| 对象缺失 | a target Object with no counterpart, or one that exists only as columns scattered across other tables |
| 定义不一致 | one term meaning different things in different modules, or one concept under several names |
| 关系不清晰 | a relation held in a free-text field, duplicated in several places, or with no enforced cardinality |
| 规则分散 | one rule implemented in several places, or only in the UI |
| 可复用 | several features that are the same Object or action under different names |

An element found only in the existing model is either dead weight or the trace of a scenario step 2 missed. Ask the user which; a missed scenario sends you back to step 2.

Done when every target element carries a verdict (一致, 不一致, or 缺失) and every existing element is matched to a target element or listed as 现有独有 with its disposition.

```md
# 产品架构差异

## 现有系统语义模型

| 元素 | 类别 | 系统内名称 | 证据 |
|---|---|---|---|
| … | 对象 | `robot_info` | `db/schema.sql:42` |

## 逐项对比

| 目标本体元素 | 现有系统对应 | 结论 | 差异种类 | 说明 | 建议 |
|---|---|---|---|---|---|
| Robot 机器人 | `robot_info`、`device` | 不一致 | 定义不一致 | … | … |

## 现有独有

| 元素 | 证据 | 处理（删除 / 补充场景 S-xx / 保留并说明） |
|---|---|---|

## 差异汇总

- 对象缺失：n 项
- 定义不一致：n 项
- 关系不清晰：n 项
- 规则分散：n 项
- 可复用：n 项
```
