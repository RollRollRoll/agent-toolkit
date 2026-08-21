# Skill mechanics

[writing-for-agents](../SKILL.md) 的 **skill 专属分支**：当这份文档是一个 skill 时，
有哪些东西会变（frontmatter、invocation 的选择，以及 router skill）。
**其余关于怎么写它的一切，都在 `SKILL.md` 那份通用参照里。**

## Invocation

两个选择，权衡的是那两种负担：

- **model-invoked（模型可触发）**的 skill **保留 `description`**，所以 agent 能自己触发它，
  别的 skill 也够得到它。**你依然可以敲它的名字**：模型可触发**总是包含**人可触发——
  一个 description 只会**多**给出 agent 的发现能力，**从不拿走**人的那条路。
  **这个 description 就是这个 skill 的顶层上下文指针，被强制一直加载着**：
  **拿永久的上下文负担，换可被发现。**
  一个内容全是参照的 model-invoked skill，**还是共享参照的一个家**：
  别的 skill 能调它，所以**好几个 skill 都需要的参照可以只住在一个地方**。
  做法：**不写 `disable-model-invocation`**，并写一段**面向模型、带上触发分支**的 description
  （`SKILL.md` 里那套写指针的规矩**全部适用**）。
- **user-invoked（只给人触发）**的 skill **把 description 从 agent 够得着的范围里拿掉**：
  **只有人敲它的名字才能触发**，别的 skill 都不行。
  **零上下文负担，但它花的是认知负担**：**你就是那个必须记得它存在的索引**。
  做法：设 `disable-model-invocation: true`；此时 `description` 变成**面向人的**——
  一句话概括，触发词清单剪掉。

**只有当 agent 必须自己够到这个 skill、或者别的 skill 必须够到它时，才选模型可触发。**
**如果它只会由人手动触发，就做成 user-invoked，一分上下文负担都别付。**

**两个 user-invoked skill 都需要的共享参照，哪一个里都住不了**：
它们都没有 description，谁也点不着谁。**把它推到 skill 体系之外的一个普通文件里**——
一份任何 skill 都能指过去的外部参照。

## 按 invocation 拆

拆分里的 invocation 这一刀（按顺序那一刀在 `SKILL.md` 里）：
**当你有一个足以独立触发它的引导词时**（一个你在自己的 prompt 里真的会用的触发词），
**或者别的 skill 必须够到它时**，就把一个 model-invoked skill 拆出去。
**你要为那条新的常驻 description 付上下文负担**，所以那份独立可达性得配得上这笔钱。

## Router skill

当 user-invoked 的 skill 多到你记不住时，那堆积起来的认知负担**由一个 router skill 来治**：
**一个 user-invoked 的 skill，点名其余那些，并说清什么时候该去拿哪一个**，
这样人只需要记住一个 skill，而不是一堆。
**它只能提示，永远点不着它们**：user-invoked 的 skill 没有 description，
除了人以外没有任何东西够得到它们。
