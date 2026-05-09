import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "render_test_plan.py"


def load_module():
    spec = importlib.util.spec_from_file_location("render_test_plan", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


SAMPLE_BUNDLE = {
    "project_name": "数据映射",
    "overview": "面向数据映射工具的一期测试计划。",
    "scope": {
        "in_scope": ["数据集选择", "AI 映射初始化", "导出预览"],
        "out_of_scope": ["上游上传解析改造"],
    },
    "test_strategy": [
        "优先覆盖核心闭环和一一对应约束。",
        "重点验证 AI 建议与人工修正切换。",
    ],
    "key_risks": [
        "Mongo 预览数据读取失败导致卡片视图不可用。",
        "并发保存导致版本覆盖。",
    ],
    "environment": {
        "test_env": "sit",
        "dependencies": ["ds-data-mapping", "model-platform", "MongoDB"],
    },
    "modules": [
        {
            "name": "映射任务",
            "requirements": [
                {
                    "title": "创建映射任务",
                    "test_points": ["必填字段校验", "AI 结果回填校验"],
                },
                {
                    "title": "保存映射任务",
                    "test_points": ["版本冲突校验"],
                },
            ],
        }
    ],
    "assumptions": ["Figma Make 原型与 PRD 无重大冲突。"],
}


class RenderTestPlanTests(unittest.TestCase):
    def test_render_test_plan_contains_expected_sections(self):
        module = load_module()

        content = module.render_test_plan(SAMPLE_BUNDLE)

        self.assertIn("# 测试计划：数据映射", content)
        self.assertIn("## 测试范围", content)
        self.assertIn("**范围内**", content)
        self.assertIn("**范围外**", content)
        self.assertIn("## 测试策略", content)
        self.assertIn("## 重点模块与测试关注点", content)
        self.assertIn("- 测试环境：sit", content)
        self.assertIn("- 依赖项：", content)
        self.assertIn("AI 映射初始化", content)
        self.assertIn("创建映射任务", content)
        self.assertIn("版本冲突校验", content)
        self.assertNotIn("{'title':", content)

    def test_write_test_plan_creates_markdown_file(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-plan.md"
            module.write_test_plan(SAMPLE_BUNDLE, output_path)

            self.assertTrue(output_path.exists())
            self.assertIn("MongoDB", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
