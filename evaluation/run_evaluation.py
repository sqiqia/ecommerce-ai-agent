import argparse
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.services.agent_service import run_ecommerce_agent
from app.services.ai_client import AIChatClient, AIClientError
from evaluation.evaluator import evaluate_response, load_cases
from evaluation.models import (
    EvaluationResult,
    FailedEvaluationResult,
)
from evaluation.reporting import (
    write_human_review_csv,
    write_json_report,
    write_markdown_report,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CASES_PATH = BASE_DIR / "cases.json"
DEFAULT_RESULTS_DIR = BASE_DIR / "results"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="验证案例，或明确确认后调用真实模型执行离线评测。"
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-paid-calls", action="store_true")
    parser.add_argument("--delay-seconds", type=float, default=0.5)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    return parser


def select_cases(cases, case_ids: list[str], limit: int | None):
    selected = cases
    if case_ids:
        wanted = set(case_ids)
        selected = [case for case in cases if case.case_id in wanted]
        missing = wanted - {case.case_id for case in selected}
        if missing:
            raise ValueError(f"没有找到案例：{', '.join(sorted(missing))}")
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit 必须大于 0")
        selected = selected[:limit]
    return selected


def print_case_overview(cases) -> None:
    profit_bands = Counter(case.expected_profit_band for case in cases)
    platforms = Counter(case.request.platform for case in cases)
    print(f"案例验证通过：{len(cases)} 条")
    print(f"利润档位分布：{dict(profit_bands)}")
    print(f"平台分布：{dict(platforms)}")


def make_ai_client() -> AIChatClient:
    missing = [
        name
        for name, value in (
            ("AI_API_KEY", settings.ai_api_key),
            ("AI_BASE_URL", settings.ai_base_url),
            ("AI_MODEL", settings.ai_model),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"缺少大模型配置：{'、'.join(missing)}")
    return AIChatClient(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        timeout_seconds=settings.ai_timeout_seconds,
    )


def execute_cases(cases, client: AIChatClient, delay_seconds: float):
    results: list[EvaluationResult] = []
    failures: list[FailedEvaluationResult] = []
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] 正在评测 {case.case_id}：{case.request.product_name}")
        started_at = time.perf_counter()
        try:
            response = run_ecommerce_agent(case.request, client)
        except AIClientError as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000)
            failures.append(
                FailedEvaluationResult(
                    case=case,
                    duration_ms=duration_ms,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
        else:
            duration_ms = round((time.perf_counter() - started_at) * 1000)
            results.append(
                EvaluationResult(
                    case=case,
                    response=response,
                    duration_ms=duration_ms,
                    automatic_checks=evaluate_response(case, response),
                )
            )
        if index < len(cases) and delay_seconds > 0:
            time.sleep(delay_seconds)
    return results, failures


def save_reports(output_dir: Path, model: str, results, failures) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"evaluation_{timestamp}.json"
    markdown_path = output_dir / f"evaluation_{timestamp}.md"
    review_path = output_dir / f"human_review_{timestamp}.csv"
    write_json_report(
        json_path,
        model=model,
        results=results,
        failures=failures,
    )
    write_markdown_report(
        markdown_path,
        model=model,
        results=results,
        failures=failures,
    )
    write_human_review_csv(review_path, results)
    return [json_path, markdown_path, review_path]


def main() -> int:
    args = build_parser().parse_args()
    try:
        cases = load_cases(args.cases)
        selected_cases = select_cases(cases, args.case_id, args.limit)
    except ValueError as exc:
        print(f"案例校验失败：{exc}")
        return 2

    print_case_overview(selected_cases)
    if not args.execute:
        print("本次只校验案例，没有调用大模型，也不会产生费用。")
        print("真实执行需要同时添加：--execute --confirm-paid-calls")
        return 0
    if not args.confirm_paid_calls:
        print("已阻止真实调用：请同时添加 --confirm-paid-calls 明确确认模型费用。")
        return 2
    if args.delay_seconds < 0:
        print("--delay-seconds 不能为负数")
        return 2

    try:
        client = make_ai_client()
    except ValueError as exc:
        print(exc)
        return 2

    print(f"即将使用模型 {client.model} 发起 {len(selected_cases)} 次真实调用。")
    results, failures = execute_cases(
        selected_cases,
        client,
        args.delay_seconds,
    )
    report_paths = save_reports(
        args.output_dir,
        client.model,
        results,
        failures,
    )
    print(f"完成：成功 {len(results)} 条，失败 {len(failures)} 条。")
    for path in report_paths:
        print(f"报告：{path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
