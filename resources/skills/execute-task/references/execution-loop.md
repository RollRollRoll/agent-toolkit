# 每任务闭环 — TDD、小步、验证、审查、提交

> 用途：`execute-task` 招牌机制「核心一」的操作细则。阶段 2 每个任务内部怎么走。
>
> **闭环**：执行 subagent 在 seam 上 TDD → 小步实现 → 验证；独立 review subagent 审查；不过则独立 fix subagent 修复 → 复审；绿后 atomic commit。一个任务一个干净闭环。

## 一 · 在 seam 上 TDD（tracer bullet）

- **tracer bullet**：一个行为测试 → 最小实现让它过 → 下一个行为。**不要**先写完所有测试再写所有实现
  （那是水平切片，测试容易和真实行为脱节）。
- **在 seam 上测**：在已约定的可测接缝（纯函数 / 接口 / 注入点，make-design / split-task 已指）上写测试，
  不去硬测难测的外壳（IO / 框架 / 网络）。
- **bug 类任务先写复现测试**：先用一个失败测试复现 bug，再修，让测试转绿——保证修对了、且不回归。
- 例：T2 先写 `test_invalid_status` / `test_empty` / `test_stable_sort` 等失败用例，再实现 `list_experiments()` 让它们绿。

## 二 · 小步推进

- 不一次写完整功能；不堆到约 100 行才第一次跑测试。
- **每一步保持系统可构建、可测**——随时能跑、能验证。
- 未完成但需合并的功能，用 **feature flag** 挡住，别让半成品阻塞主干。

## 三 · 验证节奏

按从快到慢分层验证，快的频繁跑：

- **typecheck**（若项目有）：改完随手跑，最快抓类型错。
- **单测文件**：跑当前任务相关的测试文件，确认这一片绿。
- **全套测试**：任务闭环末尾 / checkpoint 跑一次，确认没碰坏别处。
- 对齐任务的「验证方式」（split-task 已给，如 `pytest tests/test_x.py`）。

## 四 · 审查与 fix loop（各派独立 subagent）

- 执行 subagent 完成实现 + 验证后**到此为止**：不 commit、不自审；把详细报告（实现内容、测试命令与输出、
  改动文件）写进报告文件，回执只带**状态 + 一行测试摘要 + 报告路径**——状态协议与文件 handoff 细则见
  [orchestration.md](orchestration.md) 第四节。
- **审查**：主 agent 派**独立 review subagent**（fresh 上下文，只带三件套：任务简报 + 执行报告 + diff 文件）
  对照验收标准逐条审——**执行报告当未经证实的自述，以 diff 为准核对**；
  **写代码的不审自己的代码，主 agent 也不亲自审**。
- **严重度分级**：review 结论按 **Critical**（行为错 / 违反验收标准）/ **Important**（坏味道、回归风险、spec 之外的多余改动）/
  **Minor**（雕琢项）分级——**Critical / Important 清零才算审查通过**；Minor 记录在案，不阻塞闸门一。
- **修复**：有 Critical / Important → 主 agent 派**独立 fix subagent**（fresh 上下文，带 review 发现 + 同一份任务简报）修复：
  复跑覆盖其改动的测试、把修复报告（含测试命令与输出）追加进执行报告——主 agent 确认有测试证据后，
  用**新生成的 diff** 再派 review subagent 复审。
- **轮次上限**：fix → re-review 按轮次计，**默认 3 轮**；超限仍有 Critical / Important → **停下交用户判断**：
  继续修、接受现状、还是退回上游——别在原地无限循环。
- 审查关注：验收标准是否真满足、有没有引入坏味道 / 回归 / spec 之外的多余改动。

## 五 · atomic commit

- **一个任务一个原子提交**：提交粒度对齐任务，便于追溯与回滚。
- 提交信息可追溯到任务（如 `feat: list_experiments 查询+校验+稳定排序`）。
- **复审绿、过了闸门一才提交**（由主 agent 执行 commit）——验收不绿不 commit。

## 六 · bug 类任务的诊断（按需）

任务本身是修 bug 时，先诊断再改（吸收 diagnosing-bugs）：

1. 建立**紧凑反馈循环**（能快速复现）。
2. **复现并最小化**问题。
3. 提 **3~5 个可证伪假设**。
4. **定向插桩**验证假设。
5. 写**回归测试**（复现测试）。
6. 修复，并**清理调试代码**。

## 收尾自检

- 是 tracer bullet（逐行为）而非先写完所有测试？在 seam 上测？
- bug 任务先写了复现测试？
- 小步推进、每步可构建可测？
- 验证按 typecheck → 单测 → 全套分层跑了？对齐任务验证方式？
- 审查派了独立 review subagent、修复派了独立 fix subagent（没有自审自修、主 agent 没亲手审 / 修）？
- 交接走了文件三件套（简报 / 报告 / diff）？review 以 diff 为准核对了报告？fix 留了测试证据、复审用了新 diff？
- review 结论按 Critical / Important / Minor 分级了？fix loop 按轮次计、超限时停下交用户而不是无限循环？
- 复审绿、过了验收门才 atomic commit？提交信息可追溯到任务？
