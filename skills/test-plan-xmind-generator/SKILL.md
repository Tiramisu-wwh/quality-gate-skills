---
name: test-plan-xmind-generator
description: Use when QA needs to generate a test plan and native `.xmind` cause map from PRD, Figma Make, technical solution docs, API detail docs, or mixed requirement inputs, especially when the deliverable must include requirement breakdown and key test-point references as local files.
---

# 测试计划与 XMind 生成器

## 概述

当用户希望基于多份需求资料生成可复用的 QA 规划产物，而不是只在对话里临时输出一段文字时，使用这个 skill。默认产出为本地 Markdown 测试计划和一个可直接用 XMind 打开的原生 `.xmind` 文件。

## 默认行为

- 默认生成文件，而不是在聊天里展开完整计划。
- 默认按一次性流程执行：分析输入、整理标准化 bundle、写出产物。
- 如果用户要求先看草稿，就先在聊天里给短摘要，确认后再生成文件。
- 除非用户指定其他目录，否则优先输出到 `<cwd>/qa-planning/<project-name>/`。
- 默认使用通用中文测试表述，而不是沿用某个项目的内部字段名、表名或接口名。

## 支持输入

- PRD、BRD、需求 Markdown，或直接贴出的需求文本
- Figma Make 项目路径、压缩包、解压目录，或已给出的上下文
- 技术方案 Markdown 或架构说明
- 接口明细文档或接口 Markdown
- 用户给出的现有 `.xmind` 文件，用于参考样式或结构

If the request includes Figma Make, read [figma-make-intake.md](references/figma-make-intake.md).

## 输出约定

Generate at least:
- `test-plan.md`
- `<project-name>-cause-map.xmind`

The `.xmind` must contain:
- 项目根节点
- 按模块组织的二级节点
- 每个模块下的需求节点
- 每个需求下继续衍生的测试说明节点，例如 `测试点`、`注意项`、`异常`、`依赖/风险`

Use [test-plan-structure.md](references/test-plan-structure.md) for the markdown sections and [xmind-cause-map-convention.md](references/xmind-cause-map-convention.md) for node-writing rules.

## 工作流程

1. 读取用户提供的需求资料，提取以下信息：
   - 项目名称
   - 概述
   - 范围内与范围外事项
   - 测试策略
   - 关键风险
   - 环境依赖
   - 各模块下的需求列表，以及每个需求对应的测试点、注意项、异常与依赖/风险
2. 先将原始资料中的项目专有术语抽象成通用中文测试表达；只有在确实影响测试判定、联调定位或结果追溯时，才保留具体字段名、接口名、表名或系统名。
3. 组织 XMind 时，默认采用“项目 -> 模块 -> 需求 -> 测试说明”的阅读顺序，不要把“测试点”“异常”“依赖”等拆成与需求平级的大分支。
4. 按 [normalized-bundle-schema.md](references/normalized-bundle-schema.md) 中定义的轻量 JSON 结构整理这些信息。
5. 将 bundle 写入输出目录下的临时 JSON 文件。
6. 执行：

```bash
python3 scripts/generate_artifacts.py \
  --input /path/to/bundle.json \
  --output-dir /path/to/output-dir
```

7. 最终只返回简短总结、输出路径，以及假设或信息缺口。

## 先看草稿模式

当用户希望先确认再写文件时：
- 在聊天里简短总结拟定的模块拆分、主流程、关键风险和重点测试点。
- 保持简洁。
- 用户确认后，再按正常流程生成同样的本地文件。

## 编写规则

- 优先使用测试负责人视角的简洁表达，不要照搬需求原文。
- 默认采用通用中文业务/测试术语，例如“样例预览数据”“后台标准管理”“字段唯一性校验”，避免把项目内部命名直接当成正文语言。
- 项目专有字段名、接口路径、表名、服务名只在以下场景保留：影响测试判定、需要研发联调定位、需要与接口文档逐项对照。
- 如果必须保留项目专有术语，优先写成“中文说明（专有名词）”的形式，而不是整段直接堆技术名词。
- 对输入中的模糊点保留为明确假设，不要自行臆测。
- 因果图要保持测试导向，不要写成通用功能树。
- 因果图的二级节点优先只放模块，需求必须先于测试说明出现。
- 测试点、注意项、异常、依赖/风险等内容，应直接挂在对应需求下继续展开，不要再横向拆成平行大类。
- 多份输入冲突时，业务意图优先参考 PRD，技术约束优先参考技术方案和接口文档，并显式记录冲突。

## 脚本

- `scripts/render_test_plan.py`：根据标准化 bundle 渲染 Markdown 测试计划
- `scripts/build_xmind.py`：生成原生 zip 结构的 `.xmind` 文件
- `scripts/generate_artifacts.py`：一条命令生成标准产物集

## 验证

- 在声称 skill 可用之前，先运行单元测试：

```bash
python3 -m unittest discover -s tests -v
```

- 如有需要，再用真实样例文档跑一遍生成器，并确认 `.xmind` 压缩包中包含 `content.json`、`metadata.json` 和 `manifest.json`。
