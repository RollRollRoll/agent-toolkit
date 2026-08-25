---
name: domain-modeling
description: 构建和完善项目的领域模型。适用于梳理代码库术语、编写或修改 CONTEXT.md，以及记录或更新 ADR。
---

# Domain Modeling

在设计过程中持续完善项目的领域模型：检查术语是否准确，用边界场景澄清定义，
并及时记录已经确认的术语和决策。仅仅读取 `CONTEXT.md` 沿用词汇不需要调用这个 skill；
它适用于正在修改领域模型的场景。

## 文件结构

多数仓库只有一个上下文：

```text
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

如果根目录存在 `CONTEXT-MAP.md`，说明这个仓库有**多个上下文**。这张图指出每个上下文住在哪：

```text
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← 系统级决策
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← 该上下文自己的决策
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

文件按需创建。第一个术语确认后再建立 `CONTEXT.md`；第一条 ADR 确实需要记录时再建立 `docs/adr/`。

## 会话进行中要做的事

### 核对术语表

用户用的词和 `CONTEXT.md` 里已有的说法冲突时，**当场**指出来：
「你的术语表把『取消』定义成 X，但你现在说的像是 Y。到底是哪个？」

### 把含糊的话磨精确

用户用了模糊或一词多义的词，就提一个精确的规范说法：
「你说的『账户』——指的是 Customer 还是 User？这是两个东西。」

### 用具体场景检验边界

讨论领域概念之间的关系时，使用具体的边界场景检验定义，让用户明确概念之间的分界。

### 与代码核对

用户说"这块是这么工作的"时，**去看代码同不同意**。发现矛盾就摆出来：
「你的代码取消的是整个 Order，但你刚说可以部分取消。哪个是对的？」

### 当场更新 CONTEXT.md

术语一旦确认，就及时写入 `CONTEXT.md`，不要留到会话结束后集中补写。
格式见 [references/context-format.md](references/context-format.md)。

`CONTEXT.md` 只记录领域术语，不写实现细节、spec 草稿或实现决策。

### 谨慎记录 ADR

只有**三条同时成立**时，才提议写 ADR：

1. **难以逆转**：以后改主意的代价是真的有分量。
2. **不解释就显得奇怪**：将来的读者会纳闷"当初为什么要这么干？"
3. **是一次真实取舍的结果**：确实有别的选项，是出于具体理由挑了这一个。

**缺任何一条就不写。** 格式见 [references/adr-format.md](references/adr-format.md)。
