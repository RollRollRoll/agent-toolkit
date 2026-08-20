# Issue tracker：GitLab

这个仓库的 issue 与 spec 以 GitLab issue 的形式存在。
**所有操作用 [`glab`](https://gitlab.com/gitlab-org/cli) CLI。**

## 约定

- **创建 issue**：`glab issue create --title "..." --description "..."`。
  多行描述用 heredoc；传 `--description -` 会打开编辑器。
- **读 issue**：`glab issue view <number> --comments`。要机器可读就用 `-F json`。
- **列 issue**：`glab issue list -F json`，按需加 `--label` 过滤。
- **评论**：`glab issue note <number> --message "..."`。**GitLab 把评论叫 "note"。**
- **加 / 去 label**：`glab issue update <number> --label "..."` / `--unlabel "..."`。
  多个 label 可以逗号分隔，也可以重复这个 flag。
- **关闭**：`glab issue close <number>`。**`glab issue close` 不接受关闭评论**，
  所以先用 `glab issue note <number> --message "..."` 把说明发出去，再关。
- **Merge request**：**GitLab 把 PR 叫 "merge request"。** 用 `glab mr create`、`glab mr view`、
  `glab mr note` 等等——形状和 `gh pr ...` 一样，把 `pr` 换成 `mr`、
  把 `comment`/`--body` 换成 `note`/`--message`。看 diff 用 `glab mr diff <number>`。
  **和 GitHub 不同，GitLab 的 issue 与 MR 分开编号**，所以 `#42` 在知道说的是哪个面之后就没有歧义。

仓库从 `git remote -v` 推断；在克隆目录里跑时 `glab` 会自己搞定。

## 当某个 skill 说"发布到 issue tracker"时

建一个 GitLab issue。

## 当某个 skill 说"取回相关工单"时

跑 `glab issue view <number> --comments`。

## Wayfinding operations

供 `wayfinder` 使用。**地图**是单个 issue，**工单是它的子 issue**。

- **地图**：一个打了 `wayfinder:map` 标签的 issue，正文放 Notes / Decisions so far / 迷雾。
  `glab issue create --label wayfinder:map`。
  （在有原生 epic 的 GitLab 版本上，也可以用 epic 承载地图；**打标签的 issue 到处都能用**。）
- **子工单**：一个 issue，描述顶部写 `Part of #<map>`，
  标签为 `wayfinder:<type>`（`research`/`prototype`/`grilling`/`task`）。
  **一旦被认领，这张工单就指派给驱动它的那位开发者。**
- **阻塞**：用 GitLab 的**原生 blocking link**，那是**权威的、UI 里看得见**的表示。
  用 `/blocked_by #<n>` 这个 quick action 加上去，作为一条 note 发出：
  `glab issue note <child> --message "/blocked_by #<blocker>"`。
  **原生 blocking link 是 Premium / Ultimate 的功能**；免费版（或用不了的地方）
  退回到描述顶部的一行 `Blocked by: #<n>, #<n>`。
  **所有阻塞者都关闭了，这张工单才算未被阻塞。**
- **前沿查询**：`glab issue list -F json` 限定在地图的子工单范围内，
  **去掉有打开着的阻塞者的**（原生 `blocked_by` 链到一个打开着的 issue，
  用 `glab api projects/:id/issues/:iid/links` 查；或者 `Blocked by` 那行里还有打开着的 issue）
  **和有 assignee 的**；**地图顺序里排第一的胜出。**
- **认领**：`glab issue update <n> --assignee @me`，**本次会话的第一个写操作**。
- **解开**：`glab issue note <n> --message "<答案>"`，然后 `glab issue close <n>`，
  再往地图的 Decisions so far 追加一个上下文指针（要点 + 链接）。
