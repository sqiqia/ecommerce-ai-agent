import argparse
import json
from pathlib import Path

from evaluation.reporting import summarize_human_review


def main() -> int:
    parser = argparse.ArgumentParser(description="汇总人工填写的 1 到 5 分评测表。")
    parser.add_argument("review_csv", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        summary = summarize_human_review(args.review_csv)
    except (OSError, ValueError) as exc:
        print(f"人工评分汇总失败：{exc}")
        return 2

    output = json.dumps(summary, ensure_ascii=False, indent=2)
    print(output)
    if args.output is not None:
        args.output.write_text(output + "\n", encoding="utf-8")
        print(f"汇总已保存：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
