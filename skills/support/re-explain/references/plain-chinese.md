# Plain Chinese rewriting rules

> A set of Chinese writing rules you can check one by one, plus a table of common problems.
>
> **Scope**: the wording layer of a re-explanation. It governs "how to say it", not "what to say": no fact, condition, or limit may be dropped.
>
> The example sentences stay in Chinese because the output is Chinese. "病" (bad) marks the sentence to avoid; "改" (good) marks the rewrite.

## Ten rules

### 1. One idea per sentence, 30 characters max

Each sentence carries one judgment. When you see 并且 (and), 同时 (at the same time), 此外 (in addition), or 在……的情况下 (in the case of...), first check whether you can split the sentence.

### 2. Active voice, start with the verb

Most Chinese passive sentences are carried over from English. Write "系统会拒绝这个请求" (the system rejects this request), not "该请求会被系统所拒绝" (this request will be rejected by the system).

### 3. One word per concept

Fix one term and use it throughout. If one paragraph mixes "任务 / 作业 / job / task", the reader will think they are four different things.

### 4. Break up noun stacks

Three or more nouns in a row must be broken up. Turn the modifiers into a verb clause:

- 病: 用户配置同步失败重试机制
- 改: 同步用户配置失败后，会自动重试

### 5. Delete vague hedges

其实 (actually), 基本上 (basically), 某种程度上 (to some extent), 可以认为 (one could say), 相对来说 (relatively): they carry no information, so delete them all. If there really is uncertainty,
write out the uncertain **condition**: not "基本上会成功" (it will basically succeed), but "网络正常时会成功" (it succeeds when the network is working).

### 6. Avoid nested 的 chains

If a sentence has more than three 的 (the possessive/attributive particle), it is probably a nested modifier chain. Split it into two sentences.

- 病: 这是一个用于处理用户上传的文件的解析失败的兜底的流程
- 改: 文件解析失败时走这个兜底流程。文件来自用户上传。

### 7. Explain first, then use an analogy

An analogy can only be a supplement. Give the accurate explanation first, then say "打个比方" (to use an analogy).

### 8. Concrete over abstract

Give a number instead of an adjective when you can, and an example instead of a definition. Change "很慢" (very slow) to "每次要 3 秒" (3 seconds each time); change "结构复杂" (complex structure) to
"一次请求要经过 5 个服务" (one request goes through 5 services).

### 9. Explain foreign terms in Chinese the first time

The first time an English abbreviation or foreign term appears, explain what it is in one short sentence. Terms common throughout the project are exempt (such as API, CI).

### 10. Put the conclusion at the front of the sentence

Chinese habitually puts the conclusion at the end of the sentence; in a re-explanation, reverse that. Write "这条会失败，因为字段是空的" (this will fail, because the field is empty), not "因为字段是空的，所以这条会失败" (because the field is empty, this will fail).

## Bad/good sentence table

| 病 (bad) | 改 (good) | Rule broken |
|---|---|---|
| 该配置项在被同步之前会先被校验器所校验 | 同步前先校验这个配置项 | 2 |
| 其实基本上这个方案某种程度上是可行的 | 这个方案可行。前提是数据量不超过十万条 | 5 |
| 这是一个负责任务调度的任务分发作业管理组件 | 这个组件负责分发任务 | 3, 4 |
| 你可以把它理解成一个水管 | 它按顺序把消息传给下一个环节。打个比方，像一根水管 | 7 |
| 性能会有比较明显的下降 | 每次请求会多花 200 毫秒 | 8 |
| 由于缓存未命中且下游超时，因此这个请求最终失败了 | 这个请求失败了。原因是缓存没命中，下游又超时 | 10 |
