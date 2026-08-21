---
name: handoff
description: 把当前这场对话压成一份交接文档，交给另一个 agent 接手。
argument-hint: "下一场会话要用来做什么？"
disable-model-invocation: true
---

写一份交接文档，把当前这场对话总结下来，好让一个**全新的 agent** 接着把这摊活干完。
**存到用户操作系统的临时目录——不是当前工作区。**

文档里要带一节 "suggested skills"，**点名下一个 agent 该用 Skill 工具调哪些 skill**。

**已经被别的产物记下来的内容不要再重复一遍**（spec、计划、ADR、issue、commit、diff），
**改成按路径或 URL 引用它们**。

**把敏感信息脱敏**，比如 API key、口令，以及任何能识别到个人的信息。

如果用户传了参数，**把它当作"下一场会话要聚焦什么"的描述**，据此调整这份文档。
