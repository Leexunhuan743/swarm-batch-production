# Spec、Manifest 与目录约定

这份参考只补充 `SKILL.md` 中需要机械执行的布局与状态规则。项目已有成熟目录时可以映射，不要求照抄名字；但**最终交付、持久审查、权威规范、临时工作区必须逻辑分离**。

## 1. 推荐目录

```text
<project-root>/
  deliverables/                 # 最终有效产物
  spec/
    spec.md                     # 当前正式规范
    manifest.json               # 单元、角色、状态、映射的唯一台账
  reviews/
    exemplar/                   # 选定示范的对抗审查
    peer/                       # 每个批量单元两份独立互审
    vertical/                   # 纵向一致性审查
    DECISIONS.md                # 主代理的全局裁决
  work/
    drafts/                     # 可丢弃草稿/中间结果
    review-staging/             # 每个独立审查任务自己的隔离落点
```

不得把 `work/` 当成交付目录，也不要为了“干净”擅自删除用户原有文件。是否清理 `work/` 由任务和授权决定。

## 2. 稳定 ID

至少使用这些稳定标识：

- `unit_id`：被生产/审查的单元，例如 `ch-01`、`module-auth`、`case-014`。
- `agent_id`：实际作者或 reviewer 的稳定身份。
- `review_task_id`：一次独立审查任务的唯一 ID，例如 `peer__ch-07__by-agent-03`。

进入批量阶段后尽量不要修改 `unit_id`。需要改名时，在 manifest 中保留旧到新的映射。

## 3. Review 命名

### 示范审查

```text
reviews/exemplar/<unit_id>__exemplar-review__<reviewer_id>.md
```

### 标准 peer review

```text
reviews/peer/<unit_id>__peer-review__<reviewer_id>.md
```

### 纵向审查

```text
reviews/vertical/<dimension_id>__vertical-review__<reviewer_id>.md
```

同一批派工前，主代理先机械检查所有输出路径两两唯一。**同名覆盖属于数据丢失，不是命名风格问题。**

独立 peer reviewer 不直接在持久目录里边看边写，先写：

```text
work/review-staging/<review_task_id>/report.md
```

同一目标两份标准反馈都完成后，再由主代理分别提升到 `reviews/peer/`。第三方额外复核要标记为 `extra_review`，不能挤占标准两份反馈的身份。

## 4. Manifest 最小字段

默认使用 `spec/manifest.json`，因为包内 `check-manifest.py` 可以仅依赖 Python 标准库直接读取。项目已有 YAML 约定时也可以使用 `manifest.yaml` / `manifest.yml`，但运行检查器需要安装 PyYAML。其他格式可以继续使用，但应提供等价的机械核对方式。

示范单元必须在 manifest 中明确可识别。推荐同时使用：

```json
{
  "unit_id": "ch-01",
  "output": "deliverables/ch01.md",
  "author_agent": "main",
  "role": "exemplar",
  "status": "exemplar-final",
  "peer_reviewers": [],
  "peer_reviews": []
}
```

`role: "exemplar"` 适用于第一示范、随机第二示范以及明确加入的类型示范。示范制作过程中可以使用 `planned`、`drafting`、`draft_ready` 等普通前置状态；完成示范审查与修订后再进入 `status: "exemplar-final"`。`exemplar-final` 必须对应 `role: "exemplar"`，但 `role: "exemplar"` 不要求从创建起就已经 final。示范不要求阶段 6 的两份标准 peer review。

普通生产单元示例：

```json
{
  "spec_revision": "spec-r3",
  "units": [
    {
      "unit_id": "ch-01",
      "output": "deliverables/ch01.md",
      "author_agent": "main",
      "role": "exemplar",
      "status": "exemplar-final",
      "peer_reviewers": [],
      "peer_reviews": [],
      "dependencies": [],
      "exceptions": []
    },
    {
      "unit_id": "ch-07",
      "output": "deliverables/ch07.md",
      "author_agent": "agent-07",
      "role": "production",
      "status": "peer_reviewing",
      "dependencies": ["ch-06"],
      "peer_reviewers": ["agent-06", "agent-08"],
      "peer_reviews": [],
      "checks": {
        "local": "passed",
        "main_gate": "pending"
      },
      "exceptions": []
    }
  ]
}
```

长任务还要能统计每个阶段：

```text
dispatched / received / coverage_ok / failed_or_retried
```

这些数字写入台账，不依赖主代理聊天记忆。

## 5. 推荐状态

不要求复杂状态机，只需能回答“这个单元下一步能做什么”。推荐：

```text
planned
→ drafting
→ draft_ready
→ peer_reviewing
→ peer_ready        # 恰好两位不同 reviewer 的标准反馈齐全
→ revising
→ revised
→ vertically_checked
→ final
```

异常状态可另记：`blocked`、`retrying`、`author_replaced`。

关键推进规则：

- 某目标达到 `draft_ready`，且它预定的两位 reviewer 都已完成各自生产任务并保留作者上下文 → 该目标即可进入 `peer_reviewing`；不必等待无关目标。
- 若某目标的判断确实依赖全批结果，把该依赖显式记入 manifest；不要默认设置整批 barrier。
- 只有 1 份标准反馈 → 不得进入原作者修订。
- 恰好 2 份不同 reviewer 的标准反馈 → 可进入 `peer_ready`。
- 纵向审查只能在相关目标都已 `revised` 且必要门禁已复跑后开始。

## 6. Spec 最小内容

`spec/spec.md` 应来自两个已经审查并修订的基础示范，以及任何明确加入的类型示范，至少明确：

1. 任务目标与 `unit` 定义；
2. 输出路径与命名；
3. 必须统一的结构、术语、接口、字段、格式；
4. 允许变化的内容；
5. 特殊单元和合法例外；
6. 依赖、引用、输入来源；
7. 禁止修改的权威输入、spec、他人产物、review；
8. 局部自检与主代理/独立门禁；
9. 新建/自定义关键 validator 的已知通过与失败 sanity case；成熟外部工具无需重复造负例；
10. 环境能力缺失时的失败/降级预期（适用时）；
11. 两个基础示范及额外类型示范（若有）的位置；
12. 若任务存在多个结构类型，说明它们是同一 production family 下的条件变体，还是应拆成独立 family。

如果同一条 spec 在**超过半数的适用单元**中出现同方向偏离，且跨**至少两个独立作者**，必须触发一次 `spec reconciliation`。这个阈值只负责触发复核，不代表 spec 自动错误。主代理仍需回看任务目标、适用示范、机器校验和正确性依据，再决定改 spec、改示范还是改产物。若偏离集中在同一作者，优先按作者模式问题处理。明确反例或机器证据也可直接触发复核，不必等到多数。


## 7. 机械核对

`references/check-manifest.py` 只负责**确定性不变量**，不替代主代理判断。它检查：

- `unit_id` 和输出路径唯一；
- 作者、reviewer 等必要字段存在；
- reviewer 不自审，同一目标两位 reviewer 身份不同；
- 生产单元从 `peer_reviewing` 起必须已经分配两位不同 reviewer；`peer_reviewing` 期间允许 0–2 份 review 文件，进入 `peer_ready` 及后续状态时必须恰好有两份；
- review 路径不被重复引用，manifest 声明的 review 与已进入产出状态的 output 文件确实存在；从 `draft_ready` 起要求 output 文件存在，因此应先写入产物，再把状态推进到 `draft_ready`；
- `--require-final` 时所有单元都处于最终状态（`final` 或 `exemplar-final`）。

示范豁免由 `role: "exemplar"` 标识；`status: "exemplar-final"` 只表示示范已经完成，并且必须对应 `role: "exemplar"`。其他 role 值（如误写的 `first`/`second`）一律不享受豁免。

它**不检查**审查关系是否 A↔B、不猜“draft/tmp”文件名是否违规、不验证内容质量，也不根据多数票修改 spec。

推荐在阶段 0 做一次结构检查，在阶段 11 用 `--require-final` 再跑一次。若项目不用 JSON/YAML manifest，则实现同等检查即可，不必为了脚本改变项目格式。

### 批量展开前的用户反馈

如果主流程在阶段 5 前可选地邀请用户评估示范/spec，**不需要为这个检查点增加新的 manifest 状态**。只有用户反馈实际改变了全局规则时，才更新 spec revision、相关示范和必要的 `DECISIONS.md`；纯局部修改按正常示范修订处理。

## 8. `DECISIONS.md`

只记录会影响多个单元或后续代理的裁决。每条给稳定编号：

```md
## D-014 · 统一术语 X
状态：accepted
影响：ch-03, ch-07, ch-11
依据：spec-r3 + exemplar ch-01/ch-09
决定：统一使用 ...
```

拒绝意见也写一句理由，避免后续代理反复提出同一争议。

## 9. 可选导航索引

当交付物是 Markdown、HTML、文档页或其他需要浏览的多文件内容时，可以在 `deliverables/` 的父级或用户指定位置生成 `README.md`、`index.md`、`index.html` 等跳转目录。

它必须：

- 只指向最终交付，不指向 `work/`；
- 不改变正文语义；
- 不作为代码、配置、数据任务的强制步骤。
