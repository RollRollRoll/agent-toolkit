# Issue tracker：本地 Markdown

这个仓库的 issue 与 spec 以 markdown 文件的形式住在 `.scratch/` 下。

## 约定

- **一个特性一个目录**：`.scratch/<feature-slug>/`
- spec 是 `.scratch/<feature-slug>/spec.md`
- 实现类 issue **一个工单一个文件**：`.scratch/<feature-slug>/issues/<NN>-<slug>.md`，
  从 `01` 开始编号，**绝不写成一个合并的 tickets 文件**
- 评论与对话历史**追加到文件底部**的 `## Comments` 标题下

## 当某个 skill 说"发布到 issue tracker"时

在 `.scratch/<feature-slug>/` 下新建一个文件（目录不存在就建）。

## 当某个 skill 说"取回相关工单"时

读它引用的那个路径的文件。用户通常会直接把路径或 issue 编号给你。

## Wayfinding operations

供 `wayfinder` 使用。**地图**是一个文件，**每张工单一个子文件**。

- **地图**：`.scratch/<effort>/map.md`（正文含 Notes / Decisions so far / 迷雾）。
- **子工单**：`.scratch/<effort>/issues/NN-<slug>.md`，从 `01` 开始编号，正文是那个问题。
  一行 `Type:` 记工单类型（`research`/`prototype`/`grilling`/`task`）；
  一行 `Status:` 记 `claimed`/`resolved`。
- **阻塞**：顶部附近一行 `Blocked by: NN, NN`。
  **它列的每个文件都 `resolved` 了，这张工单才算未被阻塞。**
- **前沿**：扫 `.scratch/<effort>/issues/`，找出那些**打开、未被阻塞、未被认领**的文件；
  **编号最小的胜出。**
- **认领**：**动手之前**把 `Status: claimed` 写进去并保存。
- **解开**：把答案追加到 `## Answer` 标题下，把 `Status:` 改成 `resolved`，
  然后往 `map.md` 的 Decisions so far 追加一个上下文指针（要点 + 链接）。
