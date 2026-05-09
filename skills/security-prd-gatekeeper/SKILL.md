---
name: security-prd-gatekeeper
description: Use when reviewing PRD, BRD, technical design, or API documents against security checklist and SS-006 requirements before implementation, especially when an Excel review result is required.
---

# 安全设计准入评审工具

本技能用于在需求和设计阶段执行安全左移评审。它不代替代码扫描，而是检查 PRD、BRD、技术方案、接口文档、设计稿中是否已经明确了必要的安全设计要求，并生成标准 Excel 评审结果。

若用户同时提供 `PRD + Figma Make`，应联合分析：PRD 负责业务边界和要求，Figma Make 负责页面、字段、交互、接口和数据对象线索。

## 适用场景

当用户出现以下诉求时优先使用本技能：

- “帮我做安全准入”
- “根据安全 checklist 审 PRD”
- “按 SS-006 做安全设计评审”
- “做需求阶段的安全门禁”
- “评审接口设计是否满足安全规范”

## 输入材料

优先读取以下材料，能多读则多读：

- PRD / BRD
- 技术方案文档
- 接口文档 / OpenAPI / Apifox 导出文档
- Figma 设计稿中的交互与字段说明
- Figma Make 代码包 `.zip` 或已解压工程目录
- 安全部规范文件

如果用户只提供 PRD，也要照常执行，但要明确指出哪些实现相关要求在当前材料中无法确认。

## 评审标准来源

### 模板与源文件

- 模板 Excel：`assets/信息系统安全设计Checklist V1.1.xlsx`
- 评审参考：`references/CHECKLIST.md`

### 结果值约束

每一项只能填写以下四种结果之一：

- `满足`
- `不满足`
- `部分满足`
- `未涉及`

判定原则：

- `满足`：输入文档中已经明确说明控制措施、约束、流程或验收要求。
- `部分满足`：有提及，但不完整，缺少约束、异常策略、量化要求或验收口径。
- `不满足`：当前文档中未体现，而该能力对本需求是适用的。
- `未涉及`：该项对应的能力在本需求范围内明确不存在，比如没有短信验证码、没有文件上传、没有密码找回。

不要因为“实现阶段可能会做”就默认判为 `满足`。

## 工作流程

### 1. 读取评审标准

先阅读 `references/CHECKLIST.md`，理解 16 个安全域的评审边界。
若存在 Figma Make 输入，同时参考 [FIGMA_MAKE_INPUT_GUIDE.md](references/FIGMA_MAKE_INPUT_GUIDE.md)。

### 2. 分析输入文档

从文档中提取以下信息：

- 是否涉及个人敏感信息
- 是否有登录、注册、密码、验证码、文件上传下载
- 是否有接口调用、外部系统集成
- 是否涉及鉴权、权限、日志、加密、密钥、运行环境

若用户提供 Figma Make：

- 优先查看 `README.md`、入口文件、页面目录、`api`、`schema`、`types`
- 识别页面级字段、按钮、弹窗、状态切换、接口调用与数据对象
- 将这些线索作为安全设计评审的补充证据

联合输入判定原则：

- 业务规则和范围以 PRD 为主
- 页面、字段、交互和接口线索以 Figma Make 为主
- 若 PRD 未明确而 Figma Make 已体现，应判定为“有实现线索但设计要求不完整”，通常更接近 `部分满足`

### 3. 逐项评审 105 条安全要求

要求：

- 必须覆盖模板中的全部条目
- 每条都要给出 `result` 和 `note`
- `note` 用于写明证据、缺失点或判断依据

### 4. 生成 Excel 报告

必须调用 `scripts/generate_report.py` 生成 Excel 文件，不能只输出文本结论。

推荐调用方式：

```bash
python3 scripts/generate_report.py \
  --template "assets/信息系统安全设计Checklist V1.1.xlsx" \
  --output /absolute/path/安全设计评审结果.xlsx \
  --results-json /absolute/path/review_results.json \
  --project-info-json /absolute/path/project_info.json
```

其中：

- `review_results.json` 为 105 项结果字典，key 为 `1.1`、`1.2` 这样的编号
- `project_info.json` 可选，用于在摘要页展示项目名、评审人、来源文档、评审结论

### 5. 验证输出

生成后必须验证：

- 文件存在
- 文件大小正常
- `评审摘要` 工作表已生成

### 6. 对话中输出

最终回复中至少包含：

- 高风险问题摘要
- 按安全域归类的问题清单
- 最终评审结论
- Excel 文件绝对路径

## 与其他 skills 的协作

- 需要功能/接口测试用例时，衔接 `testcase-generator`
- 需要接口自动化执行时，衔接 `apifox-tests`
- 需要代码阶段安全检查时，衔接 `company-security-code-review`
- 需要综合 PRD 准入时，可先做 `prd-gatekeeper`，再做本技能
