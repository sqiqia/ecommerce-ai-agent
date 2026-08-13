from typing import Any

from pydantic import ValidationError

from app.schemas.product import (
    ExcelAnalyzeResponse,
    ExcelRowResult,
    ProductAnalyzeRequest,
)
from app.services.product_service import analyze_product
from app.utils.excel import read_product_rows


FIELD_LABELS = {
    "product_name": "商品名称",
    "sale_price": "售价",
    "cost_price": "成本",
    "shipping_fee": "运费",
    "commission_rate": "佣金率",
}

ERROR_MESSAGES = {
    "missing": "不能为空",
    "string_type": "必须是文字",
    "string_too_short": "不能为空",
    "float_type": "必须是数字",
    "float_parsing": "必须是数字",
    "greater_than": "必须大于 0",
    "greater_than_equal": "不能小于 0",
    "less_than_equal": "不能大于 1",
    "finite_number": "必须是有效数字",
}


def format_validation_error(exc: ValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors():
        field_name = str(error["loc"][-1])
        field_label = FIELD_LABELS.get(field_name, field_name)
        message = ERROR_MESSAGES.get(error["type"], error["msg"])
        messages.append(f"{field_label}{message}")
    return "；".join(messages)


def value_for_result(value: Any) -> float | str | None:
    if value is None or isinstance(value, (float, str)):
        return value
    if isinstance(value, int):
        return float(value)
    return str(value)


def analyze_excel(filename: str, content: bytes) -> ExcelAnalyzeResponse:
    results: list[ExcelRowResult] = []

    for source_row, raw_data in read_product_rows(content):
        common_fields = {
            "source_row": source_row,
            "product_name": value_for_result(raw_data.get("product_name")),
            "sale_price": value_for_result(raw_data.get("sale_price")),
            "cost_price": value_for_result(raw_data.get("cost_price")),
            "shipping_fee": value_for_result(raw_data.get("shipping_fee")),
            "commission_rate": value_for_result(raw_data.get("commission_rate")),
        }

        try:
            product = ProductAnalyzeRequest.model_validate(raw_data)
            analysis = analyze_product(product)
            validated_fields = {
                **common_fields,
                "product_name": product.product_name,
                "sale_price": product.sale_price,
                "cost_price": product.cost_price,
                "shipping_fee": product.shipping_fee,
                "commission_rate": product.commission_rate,
            }
            results.append(
                ExcelRowResult(
                    **validated_fields,
                    status="success",
                    analysis=analysis,
                )
            )
        except ValidationError as exc:
            results.append(
                ExcelRowResult(
                    **common_fields,
                    status="error",
                    error_reason=format_validation_error(exc),
                )
            )

    success_count = sum(result.status == "success" for result in results)
    return ExcelAnalyzeResponse(
        filename=filename,
        total_rows=len(results),
        success_count=success_count,
        error_count=len(results) - success_count,
        results=results,
    )
