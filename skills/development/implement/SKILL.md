---
name: implement
description: 按照已有 spec 或工单完成实现、验证和代码审查。
disable-model-invocation: true
---

完成 spec 或工单中约定的实现。

条件允许时使用 `tdd`，并在事先约定的 seam 上编写测试。

实现过程中定期运行类型检查和相关测试文件；结束前运行一次全量测试。

实现完成后，使用 `code-review` 审查本次改动。

将完成的改动提交到当前分支。
