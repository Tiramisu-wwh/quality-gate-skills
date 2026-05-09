from __future__ import annotations

import argparse
import base64
import json
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


_THUMBNAIL_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jx1sAAAAASUVORK5CYII="
)


def _legacy_content_xml(project_name: str) -> str:
    timestamp = str(int(time.time() * 1000))
    sheet_id = uuid.uuid4().hex[:26]
    root_id = uuid.uuid4().hex[:26]
    child_id = uuid.uuid4().hex[:26]
    title = escape(project_name or "未命名项目")
    warning = escape("请使用兼容 content.json 的 XMind 版本打开此文件。")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        '<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" '
        'xmlns:fo="http://www.w3.org/1999/XSL/Format" '
        'xmlns:svg="http://www.w3.org/2000/svg" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'timestamp="{timestamp}" version="2.0">'
        f'<sheet id="{sheet_id}" timestamp="{timestamp}">'
        f'<topic id="{root_id}" structure-class="org.xmind.ui.logic.right" timestamp="{timestamp}">'
        f"<title>{title}</title>"
        '<children><topics type="attached">'
        f'<topic id="{child_id}" timestamp="{timestamp}"><title>{warning}</title></topic>'
        "</topics></children>"
        "</topic>"
        "<title>画布 1</title>"
        "</sheet>"
        "</xmap-content>"
    )


def _topic(title: str, children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    topic: dict[str, Any] = {
        "id": uuid.uuid4().hex[:26],
        "class": "topic",
        "title": title,
        "attributedTitle": [{"text": title}],
    }
    if children:
        topic["children"] = {"attached": children}
    return topic


def _branch_from_items(title: str, items: list[str]) -> dict[str, Any]:
    children = [_topic(item) for item in items] if items else [_topic("未提供")]
    return _topic(title, children)


def _normalize_requirement(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        title = str(item.get("title") or item.get("name") or "未命名需求")
        notes = [str(note) for note in item.get("notes", [])]
        notes.extend(f"主流程：{flow}" for flow in item.get("core_flows", []))
        notes.extend(f"接口/数据：{interface}" for interface in item.get("interfaces", []))
        dependencies = [str(dep) for dep in item.get("dependencies", [])]
        dependencies.extend(str(risk) for risk in item.get("risks", []))
        return {
            "title": title,
            "test_points": [str(point) for point in item.get("test_points", [])],
            "notes": notes,
            "exceptions": [str(exc) for exc in item.get("exceptions", [])],
            "dependencies": dependencies,
        }
    return {
        "title": str(item),
        "test_points": [],
        "notes": [],
        "exceptions": [],
        "dependencies": [],
    }


def _detail_branches(requirement: dict[str, Any]) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    if requirement.get("test_points"):
        branches.append(_branch_from_items("测试点", requirement["test_points"]))
    if requirement.get("notes"):
        branches.append(_branch_from_items("注意项", requirement["notes"]))
    if requirement.get("exceptions"):
        branches.append(_branch_from_items("异常", requirement["exceptions"]))
    if requirement.get("dependencies"):
        branches.append(_branch_from_items("依赖/风险", requirement["dependencies"]))
    return branches or [_topic("未提供")]


def _build_sheet(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    project_name = bundle.get("project_name", "未命名项目")
    modules = bundle.get("modules", [])
    module_nodes = []

    for module in modules:
        module_name = module.get("name", "未命名模块")
        requirements = [_normalize_requirement(item) for item in module.get("requirements", [])]
        requirement_nodes = [
            _topic(requirement["title"], _detail_branches(requirement)) for requirement in requirements
        ] or [_topic("未提供")]
        module_nodes.append(_topic(module_name, requirement_nodes))

    root_topic = {
        "id": uuid.uuid4().hex[:26],
        "class": "topic",
        "title": project_name,
        "attributedTitle": [{"text": project_name}],
        "structureClass": "org.xmind.ui.logic.right",
        "children": {"attached": module_nodes or [_topic("未提供")]},
    }

    return [{"id": uuid.uuid4().hex[:26], "class": "sheet", "title": "画布 1", "rootTopic": root_topic}]


def write_xmind(bundle: dict[str, Any], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    project_name = bundle.get("project_name", "未命名项目")
    content = json.dumps(_build_sheet(bundle), ensure_ascii=False, separators=(",", ":"))
    metadata = json.dumps(
        {
            "dataStructureVersion": "2",
            "layoutEngineVersion": "3",
            "creator": {"name": "test-plan-xmind-generator", "version": "1.0"},
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    manifest = json.dumps(
        {"file-entries": {"content.json": {}, "metadata.json": {}, "Thumbnails/thumbnail.png": {}}},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    legacy_xml = _legacy_content_xml(project_name)
    thumbnail = base64.b64decode(_THUMBNAIL_PNG_BASE64)

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("content.json", content)
        archive.writestr("content.xml", legacy_xml)
        archive.writestr("metadata.json", metadata)
        archive.writestr("manifest.json", manifest)
        archive.writestr("Thumbnails/thumbnail.png", thumbnail)

    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="根据标准化测试规划数据生成原生 XMind 文件。")
    parser.add_argument("--input", required=True, help="标准化测试规划 JSON 文件路径。")
    parser.add_argument("--output", required=True, help="输出 .xmind 文件路径。")
    args = parser.parse_args()

    bundle = json.loads(Path(args.input).read_text(encoding="utf-8"))
    write_xmind(bundle, args.output)


if __name__ == "__main__":
    main()
