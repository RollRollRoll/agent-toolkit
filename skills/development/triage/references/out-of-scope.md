# Out-of-Scope 知识库

仓库里的 `.out-of-scope/` 目录存的是**被拒功能请求的持久记录**。它有两个用处：

1. **组织记忆**：一个功能**为什么**被拒，这个理由不会随着 issue 被关掉而丢失
2. **去重**：新来的 issue 与之前某次拒绝对上时，这个 skill 能把当初的决定摆出来，
   而不是把那场官司重打一遍

## 目录结构

```
.out-of-scope/
├── dark-mode.md
├── plugin-system.md
└── graphql-api.md
```

**一个概念一个文件，不是一个 issue 一个文件。** 请求同一件事的多个 issue 归到同一个文件下。

## 文件格式

这份文件要写得**松弛、好读**，更像一份短的设计文档，而不是一条数据库记录。
用段落、代码样例和例子，让**第一次撞见它的人**也能看明白这个理由，并且觉得有用。

````markdown
# Dark Mode

这个项目不支持深色模式，也不支持面向用户的主题切换。

## Why this is out of scope

渲染管线假定只有一套调色板，定义在 `ThemeConfig` 里。要支持多套主题就需要：

- 一个包住整棵组件树的 theme context provider
- 每个组件都做主题感知的样式解析
- 一层用户主题偏好的持久化

这是一次很大的架构改动，与本项目专注内容创作的取向不合。
主题是下游那些嵌入或再分发产物的消费方要操心的事。

```ts
// 现在的 ThemeConfig 接口并不是为运行时切换设计的：
interface ThemeConfig {
  colors: ColorPalette; // 单一调色板，构建期就定死了
  fonts: FontStack;
}
```

## Prior requests

- #42：「Add dark mode support」
- #87：「Night theme for accessibility」
- #134：「Dark theme option」
````

### 文件怎么命名

用**短、有描述性的 kebab-case** 概念名：`dark-mode.md`、`plugin-system.md`、`graphql-api.md`。
这个名字要**足够一眼认得出**，让浏览目录的人不打开文件也知道当初拒掉的是什么。

### 理由怎么写

理由要**有实质**：不是「我们不想要」，而是**为什么**。好的理由会引到：

- 项目范围或哲学（「这个项目专注 X；主题是下游的事」）
- 技术约束（「支持这个需要 Y，而 Y 和我们的 Z 架构冲突」）
- 战略决策（「我们选了 A 而不是 B，因为……」）

理由要**经得起时间**。**别引用临时状况**（「我们现在太忙了」）——那不是真正的拒绝，那是推迟。

## 什么时候该查 `.out-of-scope/`

triage 期间（第 1 步：收集上下文），**把 `.out-of-scope/` 下的文件全读一遍**。评估新 issue 时：

- 看这个请求**对不对得上**某个已有的 out-of-scope 概念
- **按概念相似度匹配，不是按关键词**：「night theme」对得上 `dark-mode.md`
- 对上了就**摆给维护者看**：「这个和 `.out-of-scope/dark-mode.md` 很像。
  我们当初拒它的理由是 [理由]。你现在还是这么看吗？」

维护者可能会：

- **确认**：把这个新 issue 加进已有文件的 "Prior requests" 列表，然后关掉
- **重新考虑**：删掉或更新那个 out-of-scope 文件，这个 issue 走正常 triage
- **不同意**：这两件事相关但不是一回事，走正常 triage

## 什么时候该往 `.out-of-scope/` 写

**只有当一个 enhancement（不是 bug）被拒成 `wontfix` 时。**
**enhancement 类的 PR 与 issue 一视同仁**：一个被拒的 PR 也记在这里，
免得同一个请求换成新代码再回来一次。

**不要**在某个东西因为**已经实现**而被关成 `wontfix` 时写这里。
那是一个做出来的功能，不是一个被拒的请求；把它记进来会**用假拒绝污染去重检查**。
这种情况下，关闭评论**指出这个功能已经住在哪**。

流程：

1. 维护者判定某个功能请求超出范围
2. 看有没有已经存在的匹配 `.out-of-scope/` 文件
3. 有：把这个新 issue 追加进 "Prior requests" 列表
4. 没有：新建一个文件，写上概念名、决定、理由和第一条 prior request
5. 在 issue 上发一条评论说明这个决定，并提到那个 `.out-of-scope/` 文件
6. 打上 `wontfix` 标签，关掉这个 issue

## 更新或删掉 out-of-scope 文件

如果维护者对某个之前拒掉的概念改了主意：

- 删掉那个 `.out-of-scope/` 文件
- **这个 skill 不需要去重开旧 issue**，它们是历史记录
- 触发这次重新考虑的那个新 issue 走正常 triage
