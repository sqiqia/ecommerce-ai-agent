# 离线评测使用说明

这套评测不需要真实店铺，也不需要上架商品。`cases.json` 中的价格和场景都是明确标注的模拟数据，用于检查 Agent 是否稳定遵守工作流要求。

## 已准备的案例

- 共 20 条商品案例；
- 覆盖通用、淘宝、抖音、小红书四个平台；
- 覆盖健康利润、中等利润、低利润和亏损四种状态；
- 包含“保证不晒黑”“全网最低”两条对抗输入；
- 品类包含数码、家居、箱包、宠物、运动、个护和清洁用品等。

## 第一步：零费用校验

在 PyCharm 的“终端”中执行：

```powershell
python -m evaluation.run_evaluation
```

这个命令只检查 JSON 格式、案例编号和利润档位，不调用千问，不产生费用。

## 第二步：先真实测试一条

真实调用前确认 `.env` 已配置模型。下面的命令只调用一条案例：

```powershell
python -m evaluation.run_evaluation --execute --confirm-paid-calls --limit 1
```

需要指定案例时使用：

```powershell
python -m evaluation.run_evaluation --execute --confirm-paid-calls --case-id CASE-019
```

## 第三步：运行全部20条

确认单条结果和模型费用没有问题后，才执行：

```powershell
python -m evaluation.run_evaluation --execute --confirm-paid-calls
```

结果会保存在 `evaluation/results/`，该目录已被 Git 忽略，不会把模型结果自动上传到 GitHub。

每次会生成三个文件：

1. `evaluation_时间.json`：完整输入、模型结果和自动检查；
2. `evaluation_时间.md`：成功率、工作流约定通过率、风险数量、Token、预估费用和耗时摘要；
3. `human_review_时间.csv`：人工评分表。

## 第四步：人工评分

使用 PyCharm 打开 `human_review_时间.csv`，为每条案例填写1到5分：

- `relevance`：内容是否围绕当前商品和目标用户；
- `factual_grounding`：是否只使用输入中存在的事实；
- `actionability`：行动建议是否具体；
- `platform_fit`：是否符合目标平台；
- `risk_control`：是否避免夸大和危险承诺；
- `comment`：填写扣分原因或改进意见。

五项分数需要同一行全部填写。完成后执行：

```powershell
python -m evaluation.summarize_reviews evaluation/results/human_review_你的时间.csv
```

## 指标边界

自动检查可以统计：

- 模型调用成功率；
- 工作流约定通过率；
- 平台名称是否被提及；
- 指定关键词覆盖率；
- 亏损或低利润风险是否被提及；
- 风险词命中数量和平均响应时间。
- 供应商返回的输入、输出、总 Token 和按本地配置计算的预估费用。

费用是本地估算值，不是供应商账单。请根据模型、地域和上下文长度，在 `.env` 中维护 `AI_PRICING_MODEL`、`AI_INPUT_PRICE_PER_MILLION_TOKENS` 和 `AI_OUTPUT_PRICE_PER_MILLION_TOKENS`。只有价格模型与调用模型完全一致时程序才估算费用；最新价格以[阿里云百炼官方模型价格](https://help.aliyun.com/zh/model-studio/model-pricing)为准。

这些指标不能证明销量或转化率提高。只有真实上架并完成对照实验后才能描述商业效果，本项目当前不做这种声明。
