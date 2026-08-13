from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.routes.products import analyze_uploaded_excel, read_excel_upload
from app.database.connection import get_db
from app.schemas.task import TaskDetailResponse, TaskListResponse, TaskSummaryResponse
from app.services.task_service import query_task_detail, query_tasks, save_analysis_task


router = APIRouter(prefix="/tasks", tags=["分析任务"])


@router.post(
    "/analyze-excel",
    response_model=TaskDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析商品 Excel 并保存任务",
)
async def create_analysis_task(
    file: UploadFile = File(description="需要批量分析并保存的 .xlsx 文件"),
    database: Session = Depends(get_db),
) -> TaskDetailResponse:
    filename, content = await read_excel_upload(file)
    batch = analyze_uploaded_excel(filename, content)
    saved_task = save_analysis_task(database, batch)
    task_with_results = query_task_detail(database, saved_task.id)
    return TaskDetailResponse.model_validate(task_with_results)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="查看历史任务列表",
)
def list_analysis_tasks(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    database: Session = Depends(get_db),
) -> TaskListResponse:
    total, tasks = query_tasks(database, offset=offset, limit=limit)
    return TaskListResponse(
        total=total,
        items=[TaskSummaryResponse.model_validate(task) for task in tasks],
    )


@router.get(
    "/{task_id}",
    response_model=TaskDetailResponse,
    summary="查看一个任务及其商品结果",
)
def get_analysis_task(
    task_id: int,
    database: Session = Depends(get_db),
) -> TaskDetailResponse:
    task = query_task_detail(database, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    return TaskDetailResponse.model_validate(task)
