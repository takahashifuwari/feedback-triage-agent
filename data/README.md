# 工单数据说明

种子数据来自 VS Code 集成终端的公开 GitHub Issues。每条记录用英文改写工单标题和关键症状，保留原文链接，供人工核对和关键词检索。

## 文件用途

| 文件 | 读取方 | 内容 |
| --- | --- | --- |
| `data/seed_issues.json` | 检索工具 | 30 条候选工单 |
| `eval/dev_queries.json` | 开发回放入口 | 4 条待处理反馈 |
| `eval/dev_expected.json` | 开发评估 | 预期动作、可核对的维护者记录、参考工单和追问 |

工单正文的摘要取自可核对的报告者描述。GitHub 当前公开页面未必能复原每次历史编辑。本批仅纳入正文中没有观察到事后处理结论的样例，后续遇到正文含事后线索且无法核实初始内容的工单时，应从回放样本中排除。

候选库覆盖启动失败、输入异常、终端空白和渲染异常等现象。包含相似但触发条件不同的报告，也包含晚于个别开发反馈的工单。每次回放按对应反馈的提交时间确定可查范围。比如 #239917 记录了终端分屏后的双重渲染，但它晚于 #237688，因此回放 #237688 时不可见。

## 历史工单与待处理反馈字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `issue_number` | 整数 | `microsoft/vscode` 内的工单号，用于关联来源和参考答案 |
| `created_at` | 字符串 | GitHub 创建时间，使用带 `Z` 的 UTC 时间 |
| `source_url` | 字符串 | 工单原文 |
| `title`、`symptom_summary` | 字符串 | 改写后的标题和报告者描述的现象 |
| `os_version`、`vscode_version`、`shell` | 字符串或 `null` | 报告中的系统、应用版本和终端 Shell，缺失用 `null` |
| `error_message` | 字符串或 `null` | 明确给出的报错关键字 |
| `repro_steps` | 字符串数组 | 已知复现步骤，缺失用空数组 |

开发回放按每条反馈的创建时间过滤候选，只有 `candidate.created_at < query.created_at` 的工单可参与检索。TF-IDF 默认只读取候选与反馈的标题和症状摘要，来源链接用于展示。标签、评论、重复指向和处置结果只供评估使用。

## 开发参考答案字段

`eval/dev_expected.json` 中每条反馈对应一条参考答案。每条答案都填写下列六个字段，评估程序按 `issue_number` 对照 `eval/dev_queries.json` 中的反馈。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `issue_number` | 整数 | 待处理反馈的工单号，与 `dev_queries.json` 对应 |
| `expected_action` | 字符串 | 建议的下一步。取值为 `link_existing`（建议关联）、`request_info`（先补信息）或 `create_new`（建议新建） |
| `reference_duplicate_issue_number` | 整数或 `null` | 维护者后来确认、且收录在历史候选库中的重复工单号，用于评估检索结果。没有此类目标时填 `null` |
| `evidence_url` | 字符串 | 供人工复核的 GitHub 维护者评论链接 |
| `rationale` | 字符串 | 解释为何给出该建议，可记录事后核对依据 |
| `follow_up_questions` | 字符串数组 | 建议向报告者追问的问题。无需追问时填空数组 `[]` |

例如，#293585 的 `reference_duplicate_issue_number` 是 288707，因为维护者后来确认了重复关系。凭反馈刚提交时的描述，仍要确认是输入时看不到字符，还是执行命令后没有输出，所以 `expected_action` 是 `request_info`。评估程序在 Agent 给出建议后读取参考答案。

独立评估集应避开这里的四组案例及它们已知的重复链。
