# HTML 报告格式

这份架构评审渲染成**操作系统临时目录里的一个自包含 HTML 文件**。Tailwind 和 Mermaid
都来自 CDN。**Mermaid 可靠地处理图状的图**；**手写 div 与内联 SVG 处理更有编排感的视觉**
（体量图、剖面图）。**两者混着用**：别什么都靠 Mermaid，那会开始显得很通用。

## 骨架

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Architecture review for {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      /* small custom layer for things Tailwind doesn't cover cleanly:
         dashed seam lines, hand-drawn-feeling arrow heads, etc. */
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: #dc2626; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header>...</header>
      <section id="candidates" class="space-y-10">...</section>
      <section id="top-recommendation">...</section>
    </main>
  </body>
</html>
```

## 头部

仓库名、日期，以及一份**紧凑的图例**：实线框 = module，虚线 = seam，红色箭头 = 泄漏，
粗深色框 = deep module。**不要引言段落。直接进候选项。**

## 候选项卡片

**图承担主要分量。** 文字稀疏、平实，**不加修饰地使用术语表里的词**（来自 `codebase-design` skill）。

每个候选项是一个 `<article>`：

- **标题**：短，**点名这次深化**（比如 "Collapse the Order intake pipeline"）。
- **徽章行**：推荐强度（`Strong` = emerald、`Worth exploring` = amber、`Speculative` = slate），
  外加一个**依赖类别**标签（`in-process`、`local-substitutable`、`ports & adapters`、`mock`）。
- **Files**：等宽字体列表，`font-mono text-sm`。
- **Before / After 图**：**核心**。两栏并排。套路见下。
- **Problem**：一句话。**哪里疼。**
- **Solution**：一句话。**变成什么。**
- **Wins**：要点，**每条 ≤6 个词**。比如 "Tests hit one interface"、"Pricing logic stops leaking"、
  "Delete 4 shallow wrappers"。
- **ADR 提示框**（如适用）：琥珀色底的一行。

**不要成段的解释。如果一张图需要一段话才能看懂，那就把图重画。**

## 图的套路

**挑贴合这个候选项的那一种。混着用。别让每张图都长一个样。多样性本身就是重点之一。**

### Mermaid 图（依赖 / 调用流的主力）

当重点是"X 调 Y 调 Z，看看这一团乱"时，用 Mermaid 的 `flowchart` 或 `graph`。
**用 Tailwind 样式的卡片把它裹起来**，免得它显得像空降进来的。
用 `classDef` 把泄漏的边染红、把深模块染深。
时序图很适合"before：6 次往返；after：1 次"。

```html
<div class="rounded-lg border border-slate-200 bg-white p-4">
  <pre class="mermaid">
    flowchart LR
      A[OrderHandler] --> B[OrderValidator]
      B --> C[OrderRepo]
      C -.leak.-> D[PricingClient]
      classDef leak stroke:#dc2626,stroke-width:2px;
      class C,D leak
  </pre>
</div>
```

### 手写的框与箭头（当 Mermaid 的布局跟你对着干时）

模块是带边框和标签的 `<div>`；箭头是**绝对定位在相对容器之上的内联 SVG** `<line>` 或 `<path>`。
**当你想让 "after" 那张图呈现出"一个粗边框的深模块 + 灰掉的内部"时，就用这个**——
Mermaid 渲染不出那种分量。

### 剖面图（适合分层式的浅）

把水平色带（`h-12 border-l-4`）**堆起来**，表示一次调用要穿过多少层。
Before：6 条各自什么都没干的细层。After：**1 条粗带**，标着被合并后的职责。

### 体量图（适合"接口和实现一样宽"）

**每个模块画两个矩形**：一个是**接口表面积**，一个是**实现**。
Before：接口矩形几乎和实现矩形一样高（**浅**）。After：接口矩形很矮、实现矩形很高（**深**）。

### 调用图坍缩

Before：一棵函数调用树，渲染成嵌套的框。After：**同一棵树坍缩成一个框**，
那些现在变成内部的调用**淡显在里面**。

## 风格指导

- **偏编排感，不要企业仪表盘感。** 留白充裕。标题用衬线可选
  （`font-serif` 配 stone / slate 很好）。
- **用色克制**：一个强调色（emerald 或 indigo），加上红色表泄漏、琥珀色表警告。
- 图**保持在 320px 高左右**，让 before/after 并排时不用滚动就舒服。
- 图里的模块标签用 `text-xs uppercase tracking-wider`，**让它读起来像示意图，不像 UI**。
- **唯二的脚本就是 Tailwind CDN 和 Mermaid 的 ESM import。** 报告在此之外是静态的：
  没有应用代码，除了 Mermaid 自己的渲染之外没有交互。

## Top recommendation 一节

**一张更大的卡片。** 候选项名字、一句话说明为什么、一个锚链接指向它的卡片。**就这些。**

## 语气

**大白话、简洁**，但**架构上的名词和动词直接取自 `codebase-design` skill**。
**简洁不是漂移的借口。**

**精确使用**：module、interface、implementation、depth、deep、shallow、seam、adapter、
leverage、locality。

**绝不替换**：component、service、unit（代替 module）· API、signature（代替 interface）·
boundary（代替 seam）· layer、wrapper（当你其实是指 module 时）。

**合乎风格的说法**：

- "Order intake module is shallow: interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Deepen: one interface, one place to test."
- "Two adapters justify the seam: HTTP in prod, in-memory in tests."

**Wins 那些要点要用术语表的词来点名收益**：*"locality: bugs concentrate in one module"*、
*"leverage: one interface, N call sites"*、*"interface shrinks; implementation absorbs the
wrappers"*。**别写 "easier to maintain" 或 "cleaner code"**——那些词不在术语表里，
也配不上那个位置。

**不打太极、不清嗓子、不写"值得一提的是……"。** 一句话要是能写成要点，就写成要点。
一个要点要是能砍掉，就砍掉。**一个词要是不在 `codebase-design` 的术语表里，
先去够一个在里面的，再想发明新词。**
