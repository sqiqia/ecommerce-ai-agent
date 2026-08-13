import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "ecommerce.db"


def main() -> None:
    if not DATABASE_PATH.exists():
        print(f"数据库尚未创建：{DATABASE_PATH}")
        print("请先启动服务，或调用 POST /tasks/analyze-excel。")
        return

    with sqlite3.connect(DATABASE_PATH) as connection:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' ORDER BY name"
            )
        ]
        task_count = connection.execute(
            "SELECT COUNT(*) FROM analysis_tasks"
        ).fetchone()[0]
        result_count = connection.execute(
            "SELECT COUNT(*) FROM product_results"
        ).fetchone()[0]
        latest_tasks = connection.execute(
            "SELECT id, filename, status, total_rows, success_count, "
            "error_count, created_at "
            "FROM analysis_tasks ORDER BY id DESC LIMIT 5"
        ).fetchall()

    print(f"数据库：{DATABASE_PATH}")
    print(f"数据表：{', '.join(tables)}")
    print(f"任务数量：{task_count}")
    print(f"商品结果数量：{result_count}")
    print("最近任务：")
    for task in latest_tasks:
        print(task)


if __name__ == "__main__":
    main()
