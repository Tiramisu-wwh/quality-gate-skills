from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_xmind import write_xmind
from render_test_plan import write_test_plan


def slugify_project_name(name: str) -> str:
    cleaned = name.strip().replace("/", "-")
    return cleaned or "project"


def generate_artifacts(bundle: dict, output_dir: str | Path) -> list[Path]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    project_name = slugify_project_name(bundle.get("project_name", "project"))
    plan_path = target_dir / "test-plan.md"
    xmind_path = target_dir / f"{project_name}-cause-map.xmind"

    write_test_plan(bundle, plan_path)
    write_xmind(bundle, xmind_path)

    return [plan_path, xmind_path]


def main() -> None:
    parser = argparse.ArgumentParser(description="根据标准化测试规划数据生成标准产物集。")
    parser.add_argument("--input", required=True, help="标准化测试规划 JSON 文件路径。")
    parser.add_argument("--output-dir", required=True, help="产物输出目录。")
    args = parser.parse_args()

    bundle = json.loads(Path(args.input).read_text(encoding="utf-8"))
    generated = generate_artifacts(bundle, args.output_dir)
    for path in generated:
        print(path)


if __name__ == "__main__":
    main()
