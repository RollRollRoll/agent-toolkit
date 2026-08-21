---
name: implement
description: 照一份 spec 或一组工单把一段活实现出来。
disable-model-invocation: true
---

把用户在 spec 或工单里描述的那段活实现出来。

**尽量用 `tdd`**，在事先约定好的 seam 上做。

**定期跑类型检查**，**定期跑单个测试文件**，**结束前把全量测试跑一次**。

做完之后，**用 `code-review` 审一遍这段活**。

**把你的工作提交到当前分支。**
