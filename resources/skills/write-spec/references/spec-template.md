# 行为契约 spec 模板 — 落盘用

> 用途：`write-spec` 阶段 2 起草、阶段 4 落盘时用本模板。
> 默认写到仓库既有 spec 位置；无既有约定时默认 `docs/specs/<YYYY-MM-DD>-<主题>-spec.md`。
>
> **铁律**：只写行为与验收——**不含**技术选型 / 架构 / 数据模型 / 任务拆解 / 排期。
> 唯一例外是"行为级约束"（如 MUST NOT 发起外部网络调用），它是可验证的需求，不是技术选型。
>
> **brownfield 用 delta**：改既有功能时，只写 ADDED / MODIFIED / REMOVED，不重写全系统。

## 模板（greenfield 全量）

```markdown
# Spec：<主题>

## 背景 / 范围
<为什么做（一两句）；本 spec 覆盖什么；显式不覆盖什么>

## 行为需求

### Requirement: <一句话需求标题>
系统 MUST <可观察的行为>。

#### Scenario: <场景名>
- WHEN <触发条件>
- THEN <可观察的结果（MUST ...）>

#### Scenario: <另一个场景>
- WHEN ...
- THEN ...

### Requirement: <下一条>
...

## 不做什么（MUST NOT）
- 系统 MUST NOT <禁止的行为> —— 验证：<怎么检查它没发生>
- ...

## 边界场景覆盖
- <边界类别>：<这条边界下系统 MUST 如何表现>
- ...

## 成功标准
- <可执行的检查，最好对应到"怎么跑测试">
- ...

## 待解问题
- <还没定、但需要记录、不阻塞 spec 成立的点>
```

## 模板（brownfield delta）

```markdown
# Spec（delta）：<这次改什么>

## 背景 / 范围
<为什么改；影响哪些既有行为>

## ADDED Requirements
### Requirement: <新增的行为>
系统 MUST ...
#### Scenario: ...
- WHEN ...
- THEN ...

## MODIFIED Requirements
### Requirement: <被改的行为（写改后的完整契约）>
<改前 → 改后 的差异说明（一句）>
系统 MUST ...
#### Scenario: ...
- WHEN ...
- THEN ...

## REMOVED Requirements
### Requirement: <被移除的行为>
<为什么移除；移除后 MUST 如何（如返回 404 而非旧行为）>

## 不做什么（MUST NOT）
<本次改动引入、或仍需守住的禁止项>
- 系统 MUST NOT <禁止的行为> —— 验证：<怎么检查它没发生>

## 边界场景覆盖
<本次改动涉及的边界场景（不涉及的旧场景不必重列）>
- <边界类别>：<这条边界下系统 MUST 如何表现>

## 成功标准
<本次改动怎么算做完>
- <可执行的检查，最好对应到"怎么跑测试">
```

## 写完自查

- [ ] 每条 Requirement 都有可观察的 Scenario？
- [ ] 每条 MUST NOT 都附了"怎么验证它没发生"？
- [ ] 边界场景覆盖非空（除非确实全不适用，且已确认）？
- [ ] 成功标准可执行，不是"能用就行"？
- [ ] 通篇无技术选型 / 架构 / 任务（行为级约束除外）？
- [ ] brownfield 用了 delta，没重写全系统？
