---
name: triage
description: 让 issue 与外部 PR 走过一台由 triage 角色构成的状态机：分类、验证、必要时拷问，并写出 agent 能直接开工的 brief。
disable-model-invocation: true
---

# Triage

让项目 issue tracker 上的 issue 走过一台**由 triage 角色构成的小状态机**。

如果这个仓库把外部 pull request 也当作需求入口（见 issue tracker 配置），那 triage 同样管它们：
**一个 PR 就是一个带着代码的 issue**——同一套角色、同一套状态、同一台机器，
只有下面标着「PR 的情况」的那几条不一样。光一个 `#42` 是 issue 还是 PR，**按 tracker 配置去解析**。

triage 期间**发到 issue tracker 上的每一条评论或 issue**，**必须**以这句免责声明开头：

```
> *这是 triage 过程中由 AI 生成的。*
```

## 参照文档

- [references/agent-brief.md](references/agent-brief.md)：怎么写经得起时间的 agent brief
- [references/out-of-scope.md](references/out-of-scope.md)：`.out-of-scope/` 这个知识库怎么运作

## 角色

两个**分类**角色：

- `bug`：有东西坏了
- `enhancement`：新功能或改进

五个**状态**角色：

- `needs-triage`：需要维护者评估
- `needs-info`：等报告者补更多信息
- `ready-for-agent`：规格已完整，可以交给 AFK agent
- `ready-for-human`：需要人来实现
- `wontfix`：不会去处理

**PR 的情况**：同样这些状态是**对着那份附带的代码**读的——`ready-for-agent` 意思是
brief 已经附上、agent 该在这份 diff 上走下一步；`ready-for-human` 意思是可以让人来合了。

**每个 triage 过的 issue 都应该正好带一个分类角色和一个状态角色。**
状态角色互相打架时，**先标出来问维护者**，别的什么都先别做。

这些是**标准角色名**。issue tracker 里实际用的标签字符串可能不一样，
那份映射应该已经提供给你了。如果没有，让用户去跑 `setup-env`。

**状态迁移**：没有标签的 issue 通常先进 `needs-triage`；从那里再走向 `needs-info`、
`ready-for-agent`、`ready-for-human` 或 `wontfix`。`needs-info` 在报告者回复之后**回到**
`needs-triage`。**维护者随时可以推翻**；看起来不寻常的迁移**先标出来问一句再动**。

## 调起方式

维护者调起 `triage`，用自然语言描述他要什么。**读懂这个请求，然后动手。** 比如：

- 「把需要我处理的都给我看看」
- 「来看 #42」（issue 或 PR）
- 「把 #42 挪到 ready-for-agent」
- 「有哪些是 agent 现在就能捡的？」

## 把需要处理的东西摆出来

查 issue tracker，**按三个桶呈现，最旧的排前面**：

1. **没有标签的**：从来没 triage 过。
2. **`needs-triage`**：评估进行中。
3. **`needs-info` 且报告者在上一次 triage 记录之后有过动静的**：需要重新评估。

PR 在范围内时，把外部 PR 也放进这几个桶，**每一行标上 `[PR]` 或 `[issue]`**。
**发现阶段只捞*外部* PR**（谁算外部由 tracker 配置定义），所以协作者自己在推进的 PR 不是 triage 的活。
**这个过滤只作用于发现阶段**；**被点名的 PR 无论作者是谁都照 triage 不误**。

给出计数和每项一行的摘要。**让维护者挑。**

## triage 某个具体的 issue 或 PR

1. **收集上下文。** 把这个 issue 或 PR **整个读一遍**（正文、评论、标签、作者、日期；PR 还要读 diff）。
   **把之前的 triage 记录解析出来**，免得重复问已经解决过的问题。
   用项目的领域术语表探索代码库，尊重那块区域的 ADR。**对着代码库跑两项检查**：
   (a) **重复**：**按领域概念**（而不是只按请求的措辞）搜有没有已经实现的同款行为，
   并**说明你找过哪些地方**。找到了，它就是一个「已经实现」的 `wontfix`（第 5 步）。
   (b) **之前拒过**：读 `.out-of-scope/*.md`，**把长得像这次请求的都摆出来**。

2. **给建议。** 把你的分类与状态建议连同理由告诉维护者，
   再加一段与这个请求相关的代码库摘要（包括它是不是已经实现了）。**等他给方向。**

3. **验证这个说法。** **任何拷问之前，先确认这个说法站得住。**
   bug 就照报告者给的步骤复现它。PR 就确认这份 diff 真的做到了它声称的事：切过去，跑相关的测试或命令。
   **把发生了什么如实报出来**：确认了（附代码路径）、没能确认，还是细节不足
   （**这是一个很强的 `needs-info` 信号**）。**验证过的说法能撑起一份强得多的 agent brief。**

4. **拷问（如果需要）。** 如果这个请求还需要充实，**调两次 Skill 工具**：`grilling` 和
   `domain-modeling`，**一次一轮问题**地把它拷问成形，同时打磨领域术语，
   **决定落定就当场更新 `CONTEXT.md` / ADR**。

5. **落实结果**：
   - `ready-for-agent`：发一条 agent brief 评论（[references/agent-brief.md](references/agent-brief.md)）。
   - `ready-for-human`：**结构和 agent brief 一样**，但要写明**为什么它不能交给 agent**
     （需要判断力、需要外部权限、涉及设计决策、要手工测试）。
   - `needs-info`：发一条 triage 记录（模板见下）。
   - `wontfix` 要**关掉这个 issue**，评论内容取决于**为什么**：
     - **已经实现了**：这个改动代码库里已经有了。**指出它住在哪**；
       **不要**往 `.out-of-scope/` 写（那个知识库装的是**被拒的**请求，不是已经做出来的）。
     - **被拒（bug）**：给一段客气的解释，然后关掉。
     - **被拒（enhancement）**：往 `.out-of-scope/` 写一份，从评论里链过去，然后关掉
       （[references/out-of-scope.md](references/out-of-scope.md)）。
   - `needs-triage`：打上这个角色。有部分进展的话可以附一条评论。

## 快速改状态

维护者要是说「把 #42 挪到 ready-for-agent」，**就信他，直接打上这个角色**。
**先确认你即将做什么**（改哪些角色、发什么评论、关不关），然后动手。**跳过拷问。**
如果是在没有拷问过的情况下挪到 `ready-for-agent`，**问一句他要不要写一份 agent brief**。

## needs-info 模板

```markdown
## Triage Notes

**What we've established so far:**

- 要点 1
- 要点 2

**What we still need from you (@reporter):**

- 问题 1
- 问题 2
```

**拷问期间解决掉的东西，全部记进 "established so far"**，别让那些工作丢掉。
**问题必须具体、可执行**，不能是「请提供更多信息」。

## 接着上一次的会话

如果这个 issue 或 PR 上已经有之前的 triage 记录，**读它们**，
看报告者有没有回答那些还开着的问题，**先给出一张更新过的图景，再继续**。
**不要重复问已经解决的问题。**
