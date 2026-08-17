import csv
import json
from datetime import datetime
from pathlib import Path

from evaluation.models import EvaluationResult, FailedEvaluationResult


HUMAN_SCORE_COLUMNS = (
    "relevance",
    "factual_grounding",
    "actionability",
    "platform_fit",
    "risk_control",
)


def build_summary(
    results: list[EvaluationResult],
    failures: list[FailedEvaluationResult],
) -> dict[str, int | float]:
    success_count = len(results)
    total_count = success_count + len(failures)
    contract_pass_count = sum(
        result.automatic_checks.contract_passed for result in results
    )
    guardrail_review_count = sum(
        result.automatic_checks.guardrail_status == "needs_review"
        for result in results
    )
    return {
        "total_count": total_count,
        "success_count": success_count,
        "failure_count": len(failures),
        "api_success_rate": round(success_count / total_count, 4)
        if total_count
        else 0.0,
        "contract_pass_count": contract_pass_count,
        "contract_pass_rate": round(contract_pass_count / success_count, 4)
        if success_count
        else 0.0,
        "guardrail_needs_review_count": guardrail_review_count,
        "average_duration_ms": round(
            sum(result.duration_ms for result in results) / success_count
        )
        if success_count
        else 0,
    }


def write_json_report(
    path: Path,
    *,
    model: str,
    results: list[EvaluationResult],
    failures: list[FailedEvaluationResult],
) -> None:
    report = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": model,
        "summary": build_summary(results, failures),
        "results": [result.model_dump(mode="json") for result in results],
        "failures": [failure.model_dump(mode="json") for failure in failures],
    }
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def as_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_markdown_report(
    path: Path,
    *,
    model: str,
    results: list[EvaluationResult],
    failures: list[FailedEvaluationResult],
) -> None:
    summary = build_summary(results, failures)
    lines = [
        "# 电商运营 Agent 离线评测报告",
        "",
        f"- 模型：`{model}`",
        f"- 案例数：{summary['total_count']}",
        f"- 调用成功率：{as_percent(float(summary['api_success_rate']))}",
        f"- 工作流约定通过率：{as_percent(float(summary['contract_pass_rate']))}",
        f"- 需要人工复核的风险结果：{summary['guardrail_needs_review_count']}",
        f"- 平均响应时间：{summary['average_duration_ms']} ms",
        "",
        "> 自动检查只能验证格式和明确规则，不能证明文案能提升销量。",
        "",
        "## 案例结果",
        "",
        "| 案例 | 商品 | 利润档位 | 约定检查 | 风险状态 | 耗时 |",
        "|---|---|---|---|---|---:|",
    ]
    for result in results:
        checks = result.automatic_checks
        lines.append(
            f"| {result.case.case_id} | {result.case.request.product_name} | "
            f"{result.case.expected_profit_band} | "
            f"{'通过' if checks.contract_passed else '未通过'} | "
            f"{checks.guardrail_status} | {result.duration_ms} ms |"
        )
    for failure in failures:
        lines.append(
            f"| {failure.case.case_id} | {failure.case.request.product_name} | "
            f"{failure.case.expected_profit_band} | 调用失败 | "
            f"{failure.error_type} | {failure.duration_ms} ms |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_human_review_csv(path: Path, results: list[EvaluationResult]) -> None:
    fieldnames = [
        "case_id",
        "product_name",
        "review_focus",
        "overall_assessment",
        "pricing_suggestion",
        "marketing_strategy",
        "risk_warning",
        "action_plan",
        *HUMAN_SCORE_COLUMNS,
        "comment",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            strategy = result.response.strategy
            writer.writerow(
                {
                    "case_id": result.case.case_id,
                    "product_name": result.case.request.product_name,
                    "review_focus": "；".join(result.case.review_focus),
                    "overall_assessment": strategy.overall_assessment,
                    "pricing_suggestion": strategy.pricing_suggestion,
                    "marketing_strategy": strategy.marketing_strategy,
                    "risk_warning": strategy.risk_warning,
                    "action_plan": "；".join(strategy.action_plan),
                    **{column: "" for column in HUMAN_SCORE_COLUMNS},
                    "comment": "",
                }
            )


def summarize_human_review(path: Path) -> dict[str, object]:
    """汇总已填写完整的人工评分；空白行不会被当成零分。"""

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    totals = {column: 0 for column in HUMAN_SCORE_COLUMNS}
    completed_count = 0
    for row_number, row in enumerate(rows, start=2):
        raw_scores = [row.get(column, "").strip() for column in HUMAN_SCORE_COLUMNS]
        if not any(raw_scores):
            continue
        if not all(raw_scores):
            raise ValueError(f"第 {row_number} 行的五项人工评分必须全部填写")
        try:
            scores = [int(score) for score in raw_scores]
        except ValueError as exc:
            raise ValueError(f"第 {row_number} 行评分必须是 1 到 5 的整数") from exc
        if any(score < 1 or score > 5 for score in scores):
            raise ValueError(f"第 {row_number} 行评分必须在 1 到 5 之间")
        for column, score in zip(HUMAN_SCORE_COLUMNS, scores, strict=True):
            totals[column] += score
        completed_count += 1

    averages = {
        column: round(total / completed_count, 2) if completed_count else None
        for column, total in totals.items()
    }
    return {
        "total_rows": len(rows),
        "completed_count": completed_count,
        "averages": averages,
    }
