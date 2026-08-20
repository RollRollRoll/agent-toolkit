# 什么时候该 mock

**只在系统边界上 mock**：

- 外部 API（支付、邮件等）
- 数据库（有时候——**优先用测试库**）
- 时间 / 随机性
- 文件系统（有时候）

**不要 mock**：

- 你自己的类 / 模块
- 内部协作者
- 任何你控制得了的东西

## 为可 mock 而设计

在系统边界上，把接口设计得容易 mock：

**1. 用依赖注入**

把外部依赖**传进去**，而不是在内部把它造出来：

```typescript
// 容易 mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// 难 mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. 宁可用 SDK 风格的接口，也不要一个通用 fetcher**

给**每个外部操作各写一个具体函数**，而不是写一个带条件逻辑的通用函数：

```typescript
// GOOD: 每个函数都能独立 mock
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: mock 的时候得在 mock 里面写条件逻辑
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

SDK 那种写法意味着：

- 每个 mock 只返回一种具体形状
- 测试准备里没有条件逻辑
- 一眼看得出某个测试打了哪些端点
- 每个端点各有类型安全
