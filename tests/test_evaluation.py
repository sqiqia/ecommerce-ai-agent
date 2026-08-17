import csv
import json
from collections import Counter
from pathlib import Path
from uuid import uuid4

import pytest

from app.schemas.agent import GeneratedOperationStrategy
from app.services.agent_service import run_ecommerce_agent
from evaluation.evaluator import evaluate_response, load_cases
from evaluation.models import EvaluationResult
from evaluation.reporting import (
    summarize_human_review,
    write_human_review_csv,
    write_json_report,
    write_markdown_report,
)
from evaluation.run_evaluation import main


CASES_PATH = Path("evaluation/cases.json")


class ContractCompliantClient:
    model = "fake-evaluation-model"

    def generate_structured(self, prompt, response_model):
        assert response_model is GeneratedOperationStrategy
        assert "利润计算工具结果" in prompt.user_prompt
        return GeneratedOperationStrategy(
            overall_assessment="无线鼠标适合职场人士的差旅办公场景。",
            pricing_suggestion="当前利润健康，可保持价格并小范围测试优惠。",
            marketing_strategy="在小红书围绕办公好物和便携制作真实场景内容。",
            risk_warning="不要编造销量、续航或认证信息。",
            action_plan=["拍摄差旅场景", "测试两版标题", "复盘用户反馈"],
        )


def test_default_case_set_contains_twenty_valid_cases() -> None:
    cases = load_cases(CASES_PATH)

    assert len(cases) == 20
    assert len({case.case_id for case in cases}) == 20
    assert Counter(case.expected_profit_band for case in cases) == {
        "healthy": 8,
        "medium": 9,
        "loss": 2,
        "low": 1,
    }
    assert {case.request.platform for case in cases} == {
        "通用",
        "淘宝",
        "抖音",
        "小红书",
    }


def test_case_loader_rejects_incorrect_profit_band() -> None:
    case = json.loads(CASES_PATH.read_text(encoding="utf-8"))[0]
    case["expected_profit_band"] = "loss"
    temp_directory = Path("tests/.tmp")
    temp_directory.mkdir(parents=True, exist_ok=True)
    invalid_path = temp_directory / f"invalid_cases_{uuid4().hex}.json"
    invalid_path.write_text(
        json.dumps([case], ensure_ascii=False),
        encoding="utf-8",
    )

    try:
        with pytest.raises(ValueError, match="实际计算为 healthy"):
            load_cases(invalid_path)
    finally:
        invalid_path.unlink(missing_ok=True)


def test_evaluator_checks_platform_keywords_and_contract() -> None:
    case = load_cases(CASES_PATH)[0]
    response = run_ecommerce_agent(case.request, ContractCompliantClient())

    checks = evaluate_response(case, response)

    assert checks.action_plan_count_valid is True
    assert checks.platform_mentioned is True
    assert checks.keyword_coverage_rate == 1.0
    assert checks.financial_risk_acknowledged is True
    assert checks.guardrail_status == "passed"
    assert checks.contract_passed is True


def test_low_profit_case_requires_financial_risk_language() -> None:
    case = next(
        case
        for case in load_cases(CASES_PATH)
        if case.expected_profit_band == "low"
    )

    class NoFinancialRiskClient:
        model = "fake-evaluation-model"

        def generate_structured(self, *_):
            return GeneratedOperationStrategy(
                overall_assessment="商品适合桌面使用。",
                pricing_suggestion="维持现有方案。",
                marketing_strategy="在淘宝突出桌面支架和折叠两个关键词。",
                risk_warning="发布前核对输入资料。",
                action_plan=["制作详情图", "观察用户反馈"],
            )

    response = run_ecommerce_agent(case.request, NoFinancialRiskClient())
    checks = evaluate_response(case, response)

    assert checks.financial_risk_acknowledged is False
    assert checks.contract_passed is False


def test_risky_model_output_is_recorded_for_manual_review() -> None:
    case = next(case for case in load_cases(CASES_PATH) if case.case_id == "CASE-019")

    class RiskyClient:
        model = "fake-evaluation-model"

        def generate_structured(self, *_):
            return GeneratedOperationStrategy(
                overall_assessment="当前商品亏损，不能继续按全网最低宣传。",
                pricing_suggestion="淘宝售价需要覆盖成本。",
                marketing_strategy="围绕厨房清洁和可重复使用展示场景。",
                risk_warning="全网最低属于需要人工复核的表述。",
                action_plan=["停止亏损促销", "核对商品卖点"],
            )

    response = run_ecommerce_agent(case.request, RiskyClient())
    checks = evaluate_response(case, response)

    assert checks.financial_risk_acknowledged is True
    assert checks.guardrail_status == "needs_review"
    assert checks.matched_risky_phrases == ["全网最低"]


def test_reports_and_human_review_summary() -> None:
    case = load_cases(CASES_PATH)[0]
    response = run_ecommerce_agent(case.request, ContractCompliantClient())
    result = EvaluationResult(
        case=case,
        response=response,
        duration_ms=120,
        automatic_checks=evaluate_response(case, response),
    )
    temp_directory = Path("tests/.tmp") / f"evaluation_{uuid4().hex}"
    temp_directory.mkdir(parents=True, exist_ok=True)
    json_path = temp_directory / "report.json"
    markdown_path = temp_directory / "report.md"
    review_path = temp_directory / "review.csv"

    try:
        write_json_report(
            json_path,
            model="fake-evaluation-model",
            results=[result],
            failures=[],
        )
        write_markdown_report(
            markdown_path,
            model="fake-evaluation-model",
            results=[result],
            failures=[],
        )
        write_human_review_csv(review_path, [result])

        assert json.loads(json_path.read_text(encoding="utf-8"))["summary"][
            "contract_pass_rate"
        ] == 1.0
        assert "工作流约定通过率：100.0%" in markdown_path.read_text(
            encoding="utf-8"
        )
        assert summarize_human_review(review_path)["completed_count"] == 0

        with review_path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
            fieldnames = rows[0].keys()
        for field in (
            "relevance",
            "factual_grounding",
            "actionability",
            "platform_fit",
            "risk_control",
        ):
            rows[0][field] = "5"
        with review_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        summary = summarize_human_review(review_path)
        assert summary["completed_count"] == 1
        assert summary["averages"]["relevance"] == 5.0
    finally:
        json_path.unlink(missing_ok=True)
        markdown_path.unlink(missing_ok=True)
        review_path.unlink(missing_ok=True)
        temp_directory.rmdir()


def test_execute_flag_requires_explicit_cost_confirmation(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["run_evaluation", "--execute", "--limit", "1"],
    )

    assert main() == 2
