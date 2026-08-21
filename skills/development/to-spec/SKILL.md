---
name: to-spec
description: 把当前这场对话变成一份 spec 并发布到项目的 issue tracker：不做访谈，只把你们已经聊过的东西综合起来。
disable-model-invocation: true
---

本 skill 拿**当前的对话上下文**和你对代码库的理解，产出一份 spec。
**不要访谈用户**，只把你已经知道的东西综合起来。

issue tracker 与 triage 标签词汇应该已经提供给你了。如果没有，让用户去跑 `setup-env`。

## 流程

1. 探索仓库，搞清代码库当前的状态（如果你还没探索过）。整份 spec 都用项目领域术语表里的词汇，
   并尊重你要动的那块区域的 ADR。

2. 把你打算在哪些 seam 上测这个特性勾出来。**已有的 seam 优先于新建的。用能用的最高的那个 seam。**
   如果确实需要新的 seam，就把它提在你能提的最高点上。
   **整个代码库上的 seam 越少越好——理想数量是一个。**

   **和用户确认这些 seam 是否符合他的预期。**

3. 按下面的模板写这份 spec，然后把它发布到项目的 issue tracker。
   打上 `ready-for-agent` triage 标签——不需要额外 triage。

<spec-template>

# Implementation-Ready Delivery Spec

## 文档定位

`Implementation-Ready Delivery Spec` 是进入任务拆分前的单一权威文档，负责回答三类问题：

1. **系统应该表现成什么样**：用户问题、解决方案、范围、行为需求、禁止行为、边界场景和验收标准。
2. **系统准备怎么实现**：现状基线、技术决策、组件、数据、接口、失败处理和兼容方案。
3. **如何确认实现正确**：测试原则、测试 seam、验证方式，以及需求到设计和验证的覆盖关系。


## 编写规则

1. 整份文档使用项目领域术语表中的词汇，并遵守相关 ADR。
2. 同一信息只在一个权威位置完整定义，其他章节通过 `REQ`、`SCN`、`DEC`、`VAL` 等编号引用。
3. 行为章节只描述外部可观察结果，不包含技术选型和架构。
4. 技术设计不得重新定义行为需求，只说明如何满足它们。
5. 默认描述模块、接口和契约，不枚举容易过时的具体实现文件路径。
6. 默认不嵌入实现代码。只有当原型中的状态机、Schema、Reducer 或类型形状比散文更精确地表达一项已确认决策时，才保留决策密度高的最小片段，并注明来源于原型。
7. 不提前写 task-by-task 的施工清单；设计依赖不等于任务依赖。
8. 不适用的可选章节可以删除，但必须能说明“不适用”的理由，不能因为遗漏而消失。

---

## 最小编号体系

| 类型 | 格式 | 用途 |
|---|---|---|
| 正向需求 | `REQ-001` | 系统必须提供的行为 |
| 负向需求 | `NEG-001` | 系统禁止出现的行为 |
| 质量需求 | `QOS-001` | 性能、可靠性、安全等可量化要求 |
| 场景 | `SCN-001-A` | Requirement 的可观察验收场景 |
| 技术决策 | `DEC-001` | 重大或需要追溯的技术决定 |
| 验证项 | `VAL-001` | 自动测试、基准、故障注入或人工验证 |

组件、接口和数据实体默认直接使用稳定名称，不强制增加额外编号。

---

# Implementation-Ready Delivery Spec：`<功能名称>`

```yaml
spec_id: <SPEC-ID>
related_issue: <Issue 或项目链接>
source_context:
  - <CONTEXT.md 或 CONTEXT-MAP.md>
related_adrs:
  - <ADR；没有则写 none>
last_updated: <YYYY-MM-DD>
```

---

## 1. Problem, Solution, Outcome and Scope

### 1.1 Problem

从用户视角描述当前问题。不要在这里写技术方案。

```markdown
<谁在什么情况下遇到什么问题，这个问题造成什么后果>
```

### 1.2 Solution Overview

从用户视角说明系统将提供什么能力，以及用户或上下游系统如何获得结果。不要写组件、数据库、框架或协议选型。

```markdown
<系统提供什么用户可感知的解决方式，主流程如何改善当前问题>
```

### 1.3 User Stories（按需）

提供一个**很长的、带编号的用户故事列表**。

1. 作为一个 `<actor>`，我想要 `<feature>`，以便 `<benefit>`。
2. 作为一个 `<actor>`，我想要 `<feature>`，以便 `<benefit>`。

<user-story-example>

1. 作为一名移动银行客户，我希望能够查看我的账户余额，以便我能够对自己的消费做出更明智的决策。

</user-story-example>

这份用户故事列表应该**非常全面**，覆盖该功能的所有方面。


### 1.4 In Scope

- `<本次明确建设的能力>`
- `<本次明确覆盖的主流程>`
- `<本次需要保证的兼容、迁移或运行行为>`

### 1.5 Out of Scope

- `<明确不建设的能力>`
- `<与当前问题相邻但不属于本次交付的内容>`

### 1.6 Hard Constraints

- `<兼容性约束>`
- `<性能或容量约束>`
- `<安全或合规约束>`
- `<技术栈、部署环境或依赖约束>`
- `<已经确定且不能由本次设计改变的 ADR 约束>`

### 1.7 Change Summary

| Change Type | 内容 | 对现有系统的影响 |
|---|---|---|
| Added | `<新增行为或能力>` | `<影响>` |
| Modified | `<修改行为>` | `<影响>` |
| Removed | `<移除行为>` | `<影响>` |

---

## 2. Behavioral Contract

本章是系统行为的唯一权威定义。

规范词汇：

- `MUST`：必须满足；
- `MUST NOT`：禁止发生；
- `SHOULD`：默认应满足，允许存在明确例外；
- `MAY`：允许但不强制。

可以按以下结构组织需求：

```markdown
### ADDED Requirements
### MODIFIED Requirements
### REMOVED Requirements
```

`MODIFIED` 必须写修改后的完整契约，不只写差异摘要；`REMOVED` 必须说明移除后系统如何表现。

### 2.1 Functional Requirements

#### REQ-001：`<行为标题>`

系统 MUST `<用户或外部系统可观察的行为>`。

##### SCN-001-A：`<正常场景>`

- GIVEN `<前置状态，可选>`
- WHEN `<触发条件>`
- THEN `<可观察结果>`
- AND `<额外结果，可选>`

##### SCN-001-B：`<异常或边界场景>`

- GIVEN `<前置状态>`
- WHEN `<异常、边界或竞争条件>`
- THEN `<系统必须表现出的结果>`

### 2.2 Negative Requirements

#### NEG-001：`<禁止行为标题>`

系统 MUST NOT `<禁止发生的可观察行为>`。

验证：

- `<用户、API 或外部系统层面的检查>`
- `<代码、依赖、配置或文档层面的辅助检查>`

负向需求至少要有一项用户或外部系统可观察的验证，不能只有“代码里不存在某个类”。

### 2.3 Quality Requirements（按需）

仅在存在明确、可量化的质量目标时保留。

#### QOS-001：`<质量要求标题>`

系统 MUST `<量化的性能、容量、可靠性、安全或合规目标>`。

验证：

- `<压测、基准、故障注入、审计或观测方法>`

---

## 3. Technical Design

本章回答“如何实现”，不得重新定义 §2 的系统行为。

本章描述稳定的模块、接口、数据约束和技术决策，不枚举易过时的具体实现文件路径；除非原型片段比文字更精确地表达一项已确认决策，否则不嵌入实现代码。

### 3.1 Existing Context / System Context

#### Brownfield

- 当前相关模块及职责：
- 当前主要数据流：
- 当前接口、事件和数据结构：
- 当前错误处理和运行约束：
- 已有测试 seam 与测试模式：
- 代码库中的相似实现或 Prior Art：
- 需要遵守的领域术语和 ADR：
- 不能破坏的既有行为：

#### Greenfield

- 系统边界：
- 外部参与者和外部系统：
- 外部依赖：
- 部署和运行边界：
- 主要领域上下文及关系：
- 已确定的技术栈或平台约束：

只保留与当前功能有关的现状，不重写整个系统架构。

### 3.2 Key Technical Decisions

只对重大、难逆或存在真实取舍的决策写完整 Decision。

#### DEC-001：`<技术决策标题>`

**Selected**

```markdown
<最终采用的方案>
```

**Alternatives**

- `<候选方案 A>`
- `<候选方案 B>`

**Trade-off**

| Dimension | Selected | Alternative |
|---|---|---|
| Complexity | `<评价>` | `<评价>` |
| Performance | `<评价>` | `<评价>` |
| Reliability | `<评价>` | `<评价>` |
| Maintainability | `<评价>` | `<评价>` |
| Migration Cost | `<评价>` | `<评价>` |

**Rationale**

```markdown
<为什么选择该方案，以及为什么不选择其他方案>
```

**Supports**

- `REQ-xxx`
- `NEG-xxx`
- `QOS-xxx`

**Assumptions**

- `<该决策依赖的未验证前提；没有则删除>`

**ADR**

- `<ADR 或 N/A>`

常规且容易逆转的决策可以简写为：

```markdown
- <决策点>：<选择> —— <一句理由>
```

### 3.3 Components and Data Flow

| Component | Change | Responsibility | Depends On | Supports |
|---|---|---|---|---|
| `<组件>` | Add / Modify / Remove | `<单一职责>` | `<依赖>` | `<REQ / NEG / QOS>` |

主要数据流：

```text
<入口>
  → <组件 A>
  → <组件 B>
  → <存储、外部接口或事件>
  → <结果>
```

### 3.4 Data and Interface Changes

| Item | Type | Change | Contract / Constraint | Supports |
|---|---|---|---|---|
| `<实体或接口>` | Data / API / Event / Config | Add / Modify / Remove | `<关键字段、输入输出或约束>` | `<REQ / NEG / QOS>` |

对外接口或跨模块契约需要明确：

- 输入；
- 输出；
- 错误语义；
- 幂等语义；
- 权限与数据可见性；
- 向后兼容性；
- 事件顺序、投递和去重语义。

### 3.5 State, Concurrency and Idempotency（按需）

只保留适用内容。不适用时可以删除本节，或简短说明不适用原因。

#### State Model

```text
<状态 A>
  ├─ <条件> → <状态 B>
  └─ <条件> → <状态 C>
```

#### Concurrency

- `<并发边界>`
- `<锁、版本、事务、租约或串行化方式>`
- `<不同实体或分区是否可以并行>`
- `<并发冲突如何向外部表现>`

#### Idempotency

- `<重复请求如何处理>`
- `<事件或命令如何去重>`
- `<幂等标识和有效期是什么>`

### 3.6 Error and Failure Handling

| Failure | Observable Behavior | Recovery / Degradation | Covered Scenario |
|---|---|---|---|
| `<失败情况>` | `<外部可观察结果>` | `<恢复、重试、补偿或降级>` | `<SCN>` |

失败设计至少覆盖：

- 输入或状态非法；
- 依赖超时或不可用；
- 部分成功；
- 重试和重复执行；
- 数据不一致；
- 无法自动恢复时的人工接管或安全停止。

### 3.7 Migration, Compatibility, Rollout and Rollback（按需）

Brownfield 中只要涉及数据、接口、配置或运行行为变化，本节原则上应保留。

#### Migration

- `<Schema、数据或配置迁移>`
- `<迁移顺序>`
- `<混合版本期间如何运行>`
- `<迁移失败处理>`

#### Compatibility

- `<API、事件、数据、旧客户端或混合版本兼容>`
- `<哪些旧行为必须保持>`

#### Rollout

- `<Feature Flag、灰度范围、启用顺序和观察窗口>`

#### Rollback

- `<触发条件>`
- `<代码、配置、Schema 或数据回滚>`
- `<不能回滚时的降级行为>`

### 3.8 Observability, Security and Performance（按需）

不适用的部分可以删除，不必为完整模板强行填充。

#### Observability

- 日志：
- 指标：
- Trace：
- 业务事件：
- 告警条件：
- 诊断和审计所需的关键标识：

#### Security

- 认证：
- 授权：
- 敏感数据：
- 审计：
- 主要威胁及缓解方式：

#### Performance

- 延迟预算：
- 吞吐预算：
- 容量假设：
- 资源预算：
- 性能退化边界：
- 压测或基准方法：

---

## 4. Verification and Traceability

### 4.1 Testing Principles

- 测试外部可观察行为，不绑定内部实现细节。
- 优先复用代码库中已有、且能够观察目标行为的最高层 seam。
- 只有现有 seam 无法观察关键行为时才新增 seam；新增数量应尽可能少。
- 单元测试用于纯逻辑和高组合复杂度，不替代对外部行为的集成验证。
- 每个 `SCN` 必须有验证方式，每个 `NEG` 必须有负向验证，每个 `QOS` 必须有量化证据。
- 测试设计应引用代码库中的相似测试、fixture、harness 或约定，而不是重新发明一套模式。

### 4.2 Test Seams

| Seam | Level | Reason | Prior Art | Covers |
|---|---|---|---|---|
| `<测试入口>` | Unit / Component / Integration / Contract / E2E | `<为什么在这一层测试>` | `<现有类似测试或测试模式；没有则写 none>` | `<REQ / NEG / QOS>` |

### 4.3 Verification Plan

| Verification | Requirement / Scenario | Method | Expected Result |
|---|---|---|---|
| VAL-001 | `<REQ、NEG、QOS 或 SCN>` | `<自动测试、基准、故障注入或人工检查>` | `<通过条件>` |

### 4.4 Requirement Coverage

本表是最小追踪闭环。每条本版 `REQ`、`NEG` 和 `QOS` 都必须有设计落点与验证方式。

| Requirement | Design Location | Verification | Status |
|---|---|---|---|
| REQ-001 | `<组件 / 接口 / DEC / 设计章节>` | VAL-001 | Covered |
| NEG-001 | `<设计限制 / 接口 / DEC>` | VAL-002 | Covered |
| QOS-001 | `<性能、安全或可靠性设计>` | VAL-003 | Covered |

状态只允许：

- `Covered`：设计和验证均已明确；
- `Blocked`：缺少会阻塞拆分的行为、设计或验证信息；
- `Deferred`：明确不属于本版，且已说明重访条件。

### 4.5 Verification Commands

```bash
<build command>
<unit test command>
<integration / contract / e2e test command>
<lint command>
<static analysis or other required check>
```

正式文档应使用仓库真实命令，不能保留抽象工具名。

### 4.6 Completion Criteria

- 所有本版 `REQ` 的 Scenario 通过；
- 所有 `NEG` 的负向验证通过；
- 所有 `QOS` 达到量化门槛；
- Requirement Coverage 中不存在未解释的 `Blocked`；
- Brownfield 的兼容、迁移、灰度和回滚验证通过；
- 没有无法解释的测试跳过；
- 关键日志、指标、事件和审计信息可以被观察；
- §5 Open Items 中不存在阻塞性未决问题。

---

## 5. Open Items

只记录无法归入前述章节、但对实现和评审确有价值的补充信息。不要把未解决的关键问题藏在本节中。

- `<补充说明>`

</spec-template>
