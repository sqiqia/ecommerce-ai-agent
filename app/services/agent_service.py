from app.schemas.agent import (
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
    AgentExecutionStep,
    GeneratedOperationStrategy,
)
from app.schemas.product import ProductAnalyzeRequest
from app.services.agent_prompt_service import build_agent_prompt
from app.services.ai_client import AIChatClient
from app.services.product_service import analyze_product


AGENT_VERSION = "1.0"


def run_ecommerce_agent(
    request: AgentAnalyzeRequest,
    ai_client: AIChatClient,
) -> AgentAnalyzeResponse:
    """依次执行利润工具和大模型，生成可观察的运营决策流程。"""

    product_request = ProductAnalyzeRequest(
        product_name=request.product_name,
        sale_price=request.sale_price,
        cost_price=request.cost_price,
        shipping_fee=request.shipping_fee,
        commission_rate=request.commission_rate,
    )
    product_analysis = analyze_product(product_request)

    prompt = build_agent_prompt(request, product_analysis)
    strategy = ai_client.generate_structured(prompt, GeneratedOperationStrategy)

    profit_summary = (
        f"完成利润计算：单件利润 {product_analysis.profit:.2f} 元，"
        f"利润率 {product_analysis.profit_rate_percent:.2f}%，"
        f"判断为“{product_analysis.advice}”。"
    )
    execution_trace = [
        AgentExecutionStep(
            sequence=1,
            name="理解经营目标",
            executor="agent_planner",
            summary=f"识别商品“{request.product_name}”，经营目标为“{request.business_goal}”。",
        ),
        AgentExecutionStep(
            sequence=2,
            name="调用利润计算工具",
            executor="profit_calculator",
            summary=profit_summary,
        ),
        AgentExecutionStep(
            sequence=3,
            name="生成运营策略",
            executor=ai_client.model,
            summary="将商品资料与利润工具结果发送给大模型，生成定价、营销和风险建议。",
        ),
        AgentExecutionStep(
            sequence=4,
            name="校验结构化结果",
            executor="pydantic_validator",
            summary=f"已校验运营方案格式，并生成 {len(strategy.action_plan)} 项行动计划。",
        ),
    ]

    return AgentAnalyzeResponse(
        agent_version=AGENT_VERSION,
        model=ai_client.model,
        product_analysis=product_analysis,
        strategy=strategy,
        execution_trace=execution_trace,
    )
