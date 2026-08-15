from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.copywriting import CopywritingPromptRequest
from app.schemas.product import ProductAnalyzeResponse


class AgentAnalyzeRequest(CopywritingPromptRequest):
    """电商运营 Agent 接收的完整商品和经营数据。"""

    sale_price: float = Field(
        gt=0,
        allow_inf_nan=False,
        description="商品售价，必须大于 0",
        examples=[79],
    )
    cost_price: float = Field(
        ge=0,
        allow_inf_nan=False,
        description="商品采购成本，不能为负数",
        examples=[35],
    )
    shipping_fee: float = Field(
        default=0,
        ge=0,
        allow_inf_nan=False,
        description="单件商品运费",
        examples=[8],
    )
    commission_rate: float = Field(
        default=0.05,
        ge=0,
        le=1,
        allow_inf_nan=False,
        description="平台佣金率，5% 应输入 0.05",
        examples=[0.05],
    )
    business_goal: str = Field(
        default="提升商品转化率并保持合理利润",
        min_length=1,
        max_length=150,
        description="希望 Agent 优先解决的经营目标",
    )


class AgentPrompt(BaseModel):
    """发送给大模型的运营策略提示词。"""

    prompt_version: str
    system_prompt: str
    user_prompt: str


class GeneratedOperationStrategy(BaseModel):
    """大模型必须返回的结构化运营策略。"""

    overall_assessment: str = Field(min_length=1, max_length=300)
    pricing_suggestion: str = Field(min_length=1, max_length=300)
    marketing_strategy: str = Field(min_length=1, max_length=500)
    risk_warning: str = Field(min_length=1, max_length=300)
    action_plan: list[str] = Field(min_length=2, max_length=5)


class AgentExecutionStep(BaseModel):
    """Agent 工作流中一个可观察的执行步骤。"""

    sequence: int = Field(ge=1)
    name: str
    executor: str
    status: Literal["completed"] = "completed"
    summary: str


class AgentQualityCriterion(BaseModel):
    """一次确定性质量检查的评分项。"""

    name: str
    score: int = Field(ge=0)
    max_score: int = Field(gt=0)
    explanation: str


class AgentQualityEvaluation(BaseModel):
    """Agent 结果的基础质量门禁报告。"""

    overall_score: int = Field(ge=0, le=100)
    grade: Literal["优秀", "良好", "合格", "需要优化"]
    passed: bool
    criteria: list[AgentQualityCriterion]
    suggestions: list[str]
    evaluator: str


class AgentAnalyzeResponse(BaseModel):
    """Agent 最终返回的分析、策略与执行轨迹。"""

    agent_version: str
    run_id: int | None = None
    model: str
    product_analysis: ProductAnalyzeResponse
    strategy: GeneratedOperationStrategy
    execution_trace: list[AgentExecutionStep]
    quality_evaluation: AgentQualityEvaluation | None = None


class AgentRunSummaryResponse(BaseModel):
    """Agent 历史记录列表中的摘要。"""

    id: int
    product_name: str
    business_goal: str
    model: str
    profit: float
    profit_rate_percent: float
    overall_assessment: str
    quality_score: int
    quality_grade: str
    created_at: datetime


class AgentRunDetailResponse(AgentRunSummaryResponse):
    """可用于完整回放的一次 Agent 运行记录。"""

    request: AgentAnalyzeRequest
    result: AgentAnalyzeResponse


class AgentRunListResponse(BaseModel):
    """支持分页的 Agent 历史记录列表。"""

    total: int
    items: list[AgentRunSummaryResponse]
