from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _bullet_lines(items: list[str]) -> list[str]:
    if not items:
        return ["- 未提供"]
    return [f"- {item}" for item in items]


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _normalize_requirements(module: dict[str, Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in module.get("requirements", []):
        if isinstance(item, dict):
            title = str(item.get("title") or item.get("name") or "未命名需求")
            normalized.append(
                {
                    "title": title,
                    "test_points": [str(point) for point in item.get("test_points", [])],
                }
            )
        else:
            normalized.append({"title": str(item), "test_points": []})
    return normalized


def render_test_plan(bundle: dict[str, Any]) -> str:
    project_name = bundle.get("project_name", "未命名项目")
    overview = bundle.get("overview", "未提供概述。")
    scope = bundle.get("scope", {})
    test_strategy = bundle.get("test_strategy", [])
    key_risks = bundle.get("key_risks", [])
    environment = bundle.get("environment", {})
    modules = bundle.get("modules", [])
    assumptions = bundle.get("assumptions", [])

    lines: list[str] = [
        f"# 测试计划：{project_name}",
        "",
        "## 概述",
        overview,
        "",
        "## 测试范围",
        "",
        "**范围内**",
        *_bullet_lines(scope.get("in_scope", [])),
        "",
        "**范围外**",
        *_bullet_lines(scope.get("out_of_scope", [])),
        "",
        "## 测试策略",
        *_bullet_lines(test_strategy),
        "",
        "## 重点模块与测试关注点",
    ]

    if not modules:
        lines.extend(["- 未提供模块"])
    else:
        for module in modules:
            requirements = _normalize_requirements(module)
            requirement_titles = [item["title"] for item in requirements]
            test_points = [str(point) for point in module.get("test_points", [])]
            for item in requirements:
                test_points.extend(item["test_points"])
            lines.extend(
                [
                    "",
                    f"### {module.get('name', '未命名模块')}",
                    "",
                    "**需求拆分**",
                    *_bullet_lines(requirement_titles),
                    "",
                    "**重点测试点**",
                    *_bullet_lines(_unique(test_points)),
                ]
            )

    lines.extend(
        [
            "",
            "## 风险与依赖",
            *_bullet_lines(key_risks),
            "",
            "## 测试环境",
            f"- 测试环境：{environment.get('test_env', '未指定')}",
            "- 依赖项：",
            *_bullet_lines(environment.get("dependencies", [])),
            "",
            "## 假设",
            *_bullet_lines(assumptions),
            "",
        ]
    )

    return "\n".join(lines)


def write_test_plan(bundle: dict[str, Any], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_test_plan(bundle), encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="根据标准化测试规划数据渲染 Markdown 测试计划。")
    parser.add_argument("--input", required=True, help="标准化测试规划 JSON 文件路径。")
    parser.add_argument("--output", required=True, help="输出 Markdown 文件路径。")
    args = parser.parse_args()

    bundle = json.loads(Path(args.input).read_text(encoding="utf-8"))
    write_test_plan(bundle, args.output)


if __name__ == "__main__":
    main()
