# Quality Gate Skills

公开发布的质量门禁相关 skills 仓库，按 `skills.sh` / `npx skills add` 的目录结构整理。

## Skills

- `prd-gatekeeper`
- `test-plan-xmind-generator`
- `testcase-generator`
- `apifox-tests`

## Install

安装整个仓库：

```bash
npx skills add Tiramisu-wwh/quality-gate-skills
```

按仓库 URL 安装：

```bash
npx skills add https://github.com/Tiramisu-wwh/quality-gate-skills
```

按单个 skill 安装：

```bash
npx skills add Tiramisu-wwh/quality-gate-skills --skill prd-gatekeeper
npx skills add Tiramisu-wwh/quality-gate-skills --skill test-plan-xmind-generator
npx skills add Tiramisu-wwh/quality-gate-skills --skill testcase-generator
npx skills add Tiramisu-wwh/quality-gate-skills --skill apifox-tests
```

## Prepare

- `apifox-tests/env/*.env` 已改成占位符，安装后需要自行填写 Apifox 访问令牌和环境 ID。
- `test-plan-xmind-generator`、`testcase-generator`、`prd-gatekeeper` 依赖本地 Python 环境。
- `apifox-tests` 依赖本地 Node.js 环境；首次使用前在 skill 目录执行 `npm ci`。
- 仓库中的脚本默认以相对路径运行，建议在对应 skill 目录内执行。

## Release

- 新增或调整 skill 后，先检查 `SKILL.md` frontmatter 只保留 `name` 和 `description`。
- 清理绝对路径、本地账号目录、令牌和内部链接。
- 运行最基本的验证：相关单测、`py_compile`、必要的 Node 脚本检查。
- 更新本仓库 `README.md` 的技能列表和安装示例。
- 提交后打 tag，再推送分支和 tag。

## Notes

- 公开仓库仅保留通用质量门禁 skill。
- 公司规范、条款编号、内部模板相关内容已拆到 private 仓库 `company-security-skills`。
- 这些 skills 以 Codex / Claude 类 agent 工作流为目标，部分内容默认依赖本地 Python、Node.js、Excel 模板和相关工具链。
