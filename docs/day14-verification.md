# Day 14：发布前自动验收

## 技术路线

复用现有 unittest、主案例与 evaluate.py，通过 GitHub Actions 在 Linux / Windows、Python 3.12 / 3.13 四种组合验收。CI（持续集成）指代码提交或 PR 更新后自动检查；matrix 将同一套命令展开到多个环境；artifact 是可下载的运行产物。

工作流在 PR、推送 main 或手动运行时触发。只运行离线模式；已有 Gemini 测试模拟网络响应，无需 API Key。页面由现有 Streamlit AppTest 检查，覆盖候选、交接摘要、空结果和在线失败后离线重试。

## 发布门槛

- 依赖安装和 `pip check` 成功。
- 现有 16 项测试与新增冻结评估回归测试通过。
- 主案例 #293585 可运行，候选 #288707，建议先补信息。
- 冻结评估完成 12/12、参考工单首位命中 4/4、误关联 0/8、动作正确至少 4/12。最后一项沿用离线基线下限，不代表业务可用标准。

新增测试直接复跑冻结评估，阻止“脚本能执行但指标退化”通过验收。正常改进可超过下限；修改数据或决策后，应重新审视门槛与评估说明。

## 本机复现

在项目根目录运行（Windows 可将 python 换为实际 Python 路径）：

```bash
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
python triage.py 293585
python evaluate.py --output offline-results.json
python -m pip freeze > installed-packages.txt
```

GitHub 中打开 PR 的 Checks，查看四种环境；在 Actions 对应运行的 Artifacts 下载各环境 JSON 和依赖版本清单。结果保留 14 天，发布前应下载归档。若无法运行，查看失败步骤的日志；安装失败、测试失败与模型质量问题分别处理。

requirements.txt 仍使用原有兼容范围，安装清单用于追溯每次实际版本；本次没有锁定所有依赖，也未宣称任意未来版本都可复现。

## 与 Day 13 / Day 15 的衔接

PR #13 已于 2026-11-16 13:54:14（北京时间）合并至 main，合并提交为 `3e395457f81cf6898b7df7f82f3066fe37393711`，许可证与发布说明已进入主分支。PR #14 已于 2026-11-16 14:11:25（北京时间）合并至 main，合并提交为 `4c55432907d75a27db7f0cf17a7060882c523cd0`。

Day 14 首次自动验收的四组环境已全部通过。用户已于 2026-11-16 确认本机人工验收通过。合并后 main 的自动验收运行 `43815070059` 四组环境全部通过。合并发布说明不会自动创建版本标签或 GitHub Release。

仓库仍为私有，尚未发布 v0.1.0。第十五天在确认许可证、署名和历史邮箱公开范围后，基于通过验收的提交完成首版发布。真实 Gemini 数值沿用 Day 10 的 10/12，本次 CI 不重新测量在线效果。

## 官方参考

- https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

