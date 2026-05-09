import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_artifacts.py"

SAMPLE_BUNDLE = {
    "project_name": "数据映射",
    "overview": "面向数据映射工具的一期测试计划。",
    "scope": {
        "in_scope": ["数据集选择", "AI 映射初始化", "导出预览"],
        "out_of_scope": ["上游上传解析改造"],
    },
    "test_strategy": ["优先覆盖核心闭环和一一对应约束。"],
    "key_risks": ["并发保存导致版本覆盖。"],
    "environment": {"test_env": "sit", "dependencies": ["ds-data-mapping"]},
    "modules": [
        {
            "name": "映射任务",
            "requirements": ["创建映射任务", "保存映射任务"],
            "core_flows": ["初始化映射", "导出预览"],
            "test_points": ["版本冲突校验"],
            "interfaces": ["/mapping/task/init"],
            "exceptions": ["AI 映射失败可人工修正"],
            "risks": ["上游元数据缺失"],
        }
    ],
    "cross_cutting": {"interfaces": [], "exceptions": [], "risks": []},
    "assumptions": ["Figma Make 原型与 PRD 无重大冲突。"],
}


class GenerateArtifactsTests(unittest.TestCase):
    def test_generate_artifacts_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "bundle.json"
            output_dir = Path(tmpdir) / "output"
            input_path.write_text(json.dumps(SAMPLE_BUNDLE, ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                ["python3", str(SCRIPT_PATH), "--input", str(input_path), "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "test-plan.md").exists())
            self.assertTrue((output_dir / "数据映射-cause-map.xmind").exists())

    def test_generate_artifacts_prefers_colocated_build_xmind_over_cwd_module(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "bundle.json"
            output_dir = Path(tmpdir) / "output"
            hijack_dir = Path(tmpdir) / "hijack"
            hijack_dir.mkdir()
            input_path.write_text(json.dumps(SAMPLE_BUNDLE, ensure_ascii=False), encoding="utf-8")
            (hijack_dir / "build_xmind.py").write_text(
                "\n".join(
                    [
                        "import json, zipfile",
                        "from pathlib import Path",
                        "",
                        "def write_xmind(bundle, output_path):",
                        "    target = Path(output_path)",
                        "    target.parent.mkdir(parents=True, exist_ok=True)",
                        "    with zipfile.ZipFile(target, 'w') as archive:",
                        "        archive.writestr('manifest.json', json.dumps({'file-entries': {}}))",
                        "        archive.writestr('metadata.json', json.dumps({'creator': 'hijacked'}))",
                        "        archive.writestr('content.json', '[]')",
                        "    return target",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                ["python3", str(SCRIPT_PATH), "--input", str(input_path), "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                check=False,
                cwd=hijack_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            xmind_path = output_dir / "数据映射-cause-map.xmind"
            self.assertTrue(xmind_path.exists())
            with zipfile.ZipFile(xmind_path) as archive:
                metadata = json.loads(archive.read("metadata.json").decode("utf-8"))

            self.assertEqual(metadata["creator"]["name"], "test-plan-xmind-generator")


if __name__ == "__main__":
    unittest.main()
