# 工单数据说明

种子数据来自 VS Code 集成终端的公开 GitHub Issues。每条记录用英文改写工单标题和关键症状，保留原文链接，供人工核对和关键词检索。

## 文件用途

| 文件 | 读取方 | 内容 |
| --- | --- | --- |
| `data/seed_issues.json` | 检索工具 | 4 条候选工单 |
| `eval/dev_queries.json` | 开发回放入口 | 4 条待处理反馈 |
| `eval/dev_expected.json` | 开发评估 | 预期动作、可核对的维护者记录、参考工单和追问 |

工单正文的摘要取自可核对的报告者描述。GitHub 当前公开页面未必能复原每次历史编辑。本批仅纳入正文中没有观察到事后处理结论的样例，后续遇到正文含事后线索且无法核实初始内容的工单时，应从回放样本中排除。

## 统一字段

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

`expected_action` 有三个可选值：`link_existing` 表示建议关联，`request_info` 表示先补信息，`create_new` 表示建议新建。`reference_duplicate_issue_number` 记录维护者后来确认的重复目标，用于检索核对。它可以与 `request_info` 同时出现，例如 #293585 的事后重复关系已知，但初始描述仍缺少区分输入和输出问题的信息。独立评估集应避开这里的四组案例及它们已知的重复链。
