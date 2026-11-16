# v0.1.0 · 首个开源版本

客户反馈分流 Agent 面向客服和产品运营。首版用 VS Code 集成终端的公开工单演示如何找历史问题、提出追问并把判断交给经办人核对。

## 主要功能

- 通过 Streamlit 网页选择样例或提交英文反馈，查看最多三条历史候选及原文链接。
- 使用 TF-IDF、余弦相似度和离线规则给出分流建议。配置 Gemini 后可生成判断依据和具体追问，在线请求失败时可切回离线规则。
- 在网页编辑并复制交接摘要。也可从终端回放单个案例，或生成批量评估的 JSON。

## 评估

在 12 条冻结样例上，离线规则动作正确 4/12，Gemini 3.5 Flash Lite 动作正确 10/12。两种模式使用同一批候选，4 条参考工单均排在第一。Gemini 的两条错误是把仍需追问的反馈判成建议新建。样例三类均衡选取，结果用于比较本项目两种模式。[逐例结果](eval/day10_results.md)

## 运行

使用 Python 3.12 或 3.13。下载并解压代码后，在含 `app.py` 的目录运行：

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

默认以离线规则演示。Gemini 配置、命令行示例和评估复现见 [README](README.md)。项目代码采用 [MIT 许可证](LICENSE)。
