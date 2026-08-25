---
name: handoff
description: 将当前对话整理成简明的交接文档，供另一个 agent 继续处理。
argument-hint: "下一场会话要用来做什么？"
disable-model-invocation: true
---

将当前对话整理成一份交接文档，让没有前序上下文的 agent 可以继续完成这项工作。
文档存到用户操作系统的临时目录，不要放进当前工作区。

文档中加入 `suggested skills` 小节，列出接手的 agent 应调用哪些 skill。

spec、计划、ADR、issue、commit 或 diff 已经记录的内容无需重复，改用路径或 URL 引用。

对 API key、口令和个人身份信息等敏感内容进行脱敏。

如果用户传入参数，将其视为下一场会话的关注重点，并据此调整交接内容。
