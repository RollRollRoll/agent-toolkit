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

## Problem Statement

用户正面对的那个问题，**从用户的视角**写。

## Solution

这个问题的解法，**从用户的视角**写。

## User Stories

一份**很长的**、带编号的用户故事清单。每条用户故事的格式是：

1. 作为一个 <actor>，我想要 <feature>，以便 <benefit>

<user-story-example>
1. 作为一个手机银行客户，我想要看到我各个账户的余额，以便我能对自己的花销做出更明智的决定
</user-story-example>

这份用户故事清单应当**极其详尽**，覆盖这个特性的所有方面。

## Implementation Decisions

已经做出的实现决策清单。可以包括：

- 会新建 / 改动哪些模块
- 那些模块里会被改动的接口
- 来自开发者的技术澄清
- 架构决策
- schema 变更
- API 契约
- 具体的交互

**不要写具体的文件路径或代码片段**，它们很可能很快就过时。

例外：如果某个原型产出的片段，比散文更精确地编码了一个决策（状态机、reducer、schema、类型形状），
就把它内联在对应的那条决策里，并简短注明它来自一个原型。
**剪到决策密度高的那部分**——不是一个能跑的 demo，只要那些要紧的部分。

## Testing Decisions

已经做出的测试决策清单。要包括：

- 一段关于什么算好测试的说明（只测外部行为，不测实现细节）
- 哪些模块会被测
- 这些测试的先例（也就是代码库里同类型的测试）

## Out of Scope

这份 spec 把哪些东西划在范围之外。

## Further Notes

关于这个特性的其他补充说明。

</spec-template>
