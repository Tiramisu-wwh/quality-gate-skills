import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_xmind.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_xmind", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


SAMPLE_BUNDLE = {
    "project_name": "数据映射",
    "modules": [
        {
            "name": "映射任务",
            "requirements": [
                {
                    "title": "创建映射任务",
                    "test_points": ["必填字段校验", "AI 理由展示"],
                    "notes": ["主流程：选择数据集后初始化映射", "接口/数据：POST /mapping/task/init"],
                    "exceptions": ["AI 映射失败时允许人工修正"],
                    "dependencies": ["依赖 model-platform 返回推荐结果"],
                },
                {
                    "title": "导出预览",
                    "test_points": ["导出结构与当前保存结果一致"],
                    "notes": ["接口/数据：POST /mapping/export/preview"],
                    "exceptions": ["大数据量时预览超时需提示重试"],
                    "dependencies": ["依赖 ds-data-mapping 读取已保存映射"],
                },
            ],
        }
    ],
}


class BuildXMindTests(unittest.TestCase):
    def test_write_xmind_creates_native_package(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cause-map.xmind"
            module.write_xmind(SAMPLE_BUNDLE, output_path)

            self.assertTrue(output_path.exists())
            with zipfile.ZipFile(output_path) as archive:
                names = set(archive.namelist())
                self.assertIn("content.json", names)
                self.assertIn("content.xml", names)
                self.assertIn("manifest.json", names)
                self.assertIn("metadata.json", names)
                self.assertIn("Thumbnails/thumbnail.png", names)

    def test_generated_content_json_contains_module_requirement_structure(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cause-map.xmind"
            module.write_xmind(SAMPLE_BUNDLE, output_path)

            with zipfile.ZipFile(output_path) as archive:
                content = json.loads(archive.read("content.json").decode("utf-8"))

            root_children = content[0]["rootTopic"]["children"]["attached"]
            self.assertEqual([node["title"] for node in root_children], ["映射任务"])

            module_node = root_children[0]
            requirement_titles = [node["title"] for node in module_node["children"]["attached"]]
            self.assertEqual(requirement_titles, ["创建映射任务", "导出预览"])

            first_requirement = module_node["children"]["attached"][0]
            detail_titles = [node["title"] for node in first_requirement["children"]["attached"]]
            self.assertEqual(detail_titles, ["测试点", "注意项", "异常", "依赖/风险"])

            notes_branch = first_requirement["children"]["attached"][1]
            note_values = [node["title"] for node in notes_branch["children"]["attached"]]
            self.assertIn("主流程：选择数据集后初始化映射", note_values)
            self.assertIn("接口/数据：POST /mapping/task/init", note_values)

    def test_generated_package_uses_xmind_compatible_manifest_and_metadata(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cause-map.xmind"
            module.write_xmind(SAMPLE_BUNDLE, output_path)

            with zipfile.ZipFile(output_path) as archive:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
                metadata = json.loads(archive.read("metadata.json").decode("utf-8"))

            self.assertEqual(
                manifest,
                {
                    "file-entries": {
                        "content.json": {},
                        "metadata.json": {},
                        "Thumbnails/thumbnail.png": {},
                    }
                },
            )
            self.assertEqual(metadata["dataStructureVersion"], "2")
            self.assertEqual(metadata["layoutEngineVersion"], "3")
            self.assertIn("name", metadata["creator"])
            self.assertIn("version", metadata["creator"])


if __name__ == "__main__":
    unittest.main()
