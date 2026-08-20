# CONTEXT.md 格式

## 结构

```md
# {上下文名称}

{一两句话说明这个上下文是什么、为什么存在。}

## Language

**Order**：
{一两句话说明这个术语是什么}
_Avoid_: Purchase, transaction

**Invoice**：
交付之后发给客户的付款请求。
_Avoid_: Bill, payment request

**Customer**：
下订单的个人或组织。
_Avoid_: Client, buyer, account
```

## 规则

- **要有立场。** 同一个概念有多个说法时，**挑一个最好的**，其余的列进 `_Avoid_`。
- **定义要紧。** 最多一两句。写它**是什么**，不写它**做什么**。
- **只收这个上下文独有的术语。** 通用编程概念（超时、错误类型、工具模式）不进来，
  哪怕项目里用得再多。加词之前先问：**这是本上下文独有的概念，还是通用编程概念？**
  只有前者该进。
- **自然聚成簇时用小标题分组。** 如果所有术语本来就属于同一个内聚区域，平铺一份列表就够。

## 单上下文 vs 多上下文仓库

**单上下文（多数仓库）**：仓库根目录一份 `CONTEXT.md`。

**多上下文**：根目录一份 `CONTEXT-MAP.md`，列出有哪些上下文、各自住在哪、彼此什么关系：

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md)：接收并跟踪客户订单
- [Billing](./src/billing/CONTEXT.md)：生成发票并处理付款
- [Fulfillment](./src/fulfillment/CONTEXT.md)：管理仓库拣货与发货

## Relationships

- **Ordering → Fulfillment**：Ordering 发出 `OrderPlaced` 事件，Fulfillment 消费它来启动拣货
- **Fulfillment → Billing**：Fulfillment 发出 `ShipmentDispatched` 事件，Billing 消费它来生成发票
- **Ordering ↔ Billing**：共享 `CustomerId` 与 `Money` 类型
```

用哪种结构由你**自己推断**：

- 有 `CONTEXT-MAP.md` → 读它去找各个上下文；
- 只有根目录的 `CONTEXT.md` → 单上下文；
- 两个都没有 → **等第一个术语定下来时**，按需在根目录创建 `CONTEXT.md`。

存在多个上下文时，**推断当前话题属于哪一个**。判断不了就问。
