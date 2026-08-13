from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.schemas.product import (
    ExcelAnalyzeResponse,
    ProductAnalyzeRequest,
    ProductAnalyzeResponse,
)
from app.services.excel_service import analyze_excel
from app.services.product_service import analyze_product
from app.utils.excel import ExcelValidationError, build_result_workbook


router = APIRouter(prefix="/products", tags=["商品分析"])
MAX_EXCEL_SIZE = 5 * 1024 * 1024
EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.post(
    "/analyze",
    response_model=ProductAnalyzeResponse,
    summary="分析单个商品的利润",
)
def analyze_product_endpoint(
    product: ProductAnalyzeRequest,
) -> ProductAnalyzeResponse:
    return analyze_product(product)


async def read_excel_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = file.filename or "products.xlsx"
    if Path(filename).suffix.lower() != ".xlsx":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 .xlsx 格式的 Excel 文件",
        )

    content = await file.read(MAX_EXCEL_SIZE + 1)
    await file.close()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传文件不能为空",
        )
    if len(content) > MAX_EXCEL_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Excel 文件不能超过 5MB",
        )
    return filename, content


def analyze_uploaded_excel(filename: str, content: bytes) -> ExcelAnalyzeResponse:
    try:
        return analyze_excel(filename, content)
    except ExcelValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/analyze-excel",
    response_model=ExcelAnalyzeResponse,
    summary="上传并批量分析商品 Excel",
)
async def analyze_excel_endpoint(
    file: UploadFile = File(description="包含商品名称、售价、成本、运费、佣金率的 .xlsx 文件"),
) -> ExcelAnalyzeResponse:
    filename, content = await read_excel_upload(file)
    return analyze_uploaded_excel(filename, content)


@router.post(
    "/analyze-excel/export",
    summary="上传商品 Excel 并下载分析结果",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "处理完成后的 Excel 文件",
            "content": {
                EXCEL_MEDIA_TYPE: {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        }
    },
)
async def export_excel_endpoint(
    file: UploadFile = File(description="包含商品名称、售价、成本、运费、佣金率的 .xlsx 文件"),
) -> StreamingResponse:
    filename, content = await read_excel_upload(file)
    batch = analyze_uploaded_excel(filename, content)
    result_content = build_result_workbook(batch)
    return StreamingResponse(
        BytesIO(result_content),
        media_type=EXCEL_MEDIA_TYPE,
        headers={
            "Content-Disposition": 'attachment; filename="product_analysis_result.xlsx"'
        },
    )
