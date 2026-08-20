# 好测试与坏测试

## 好测试

**集成风格**：通过**真实接口**测，而不是 mock 掉内部零件。

```typescript
// GOOD: 测的是可观察的行为
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

特征：

- 测的是用户 / 调用方在乎的行为
- 只用公开 API
- 扛得住内部重构
- 描述的是 **WHAT**，不是 **HOW**
- 一个测试一个逻辑断言

## 坏测试

**实现细节测试**：与内部结构耦合。

```typescript
// BAD: 测的是实现细节
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

危险信号：

- mock 内部协作者
- 测私有方法
- 断言调用次数 / 调用顺序
- 行为没变、只是重构，测试就挂了
- 测试名描述的是 HOW 而不是 WHAT
- 绕过接口、用外部手段来验证

```typescript
// BAD: 绕过接口去验证
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: 通过接口验证
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

**同义反复的测试**：期望值把实现重述了一遍，于是这个测试**天生就会通过**。

```typescript
// BAD: 期望值是用代码同样的方式重算出来的
test("calculateTotal sums line items", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// GOOD: 期望值是一个独立的、已知的字面量
test("calculateTotal sums line items", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```
