# Quality Gate Skills

公开发布的质量门禁相关 skills 仓库，按 `skills.sh` / `npx skills add` 的目录结构整理。

## Skills

- `prd-gatekeeper`
- `security-prd-gatekeeper`
- `test-plan-xmind-generator`
- `testcase-generator`
- `company-security-code-review`
- `apifox-tests`

## Install

安装整个仓库：

```bash
npx skills add Tiramisu-wwh/quality-gate-skills
```

按单个 skill 安装：

```bash
npx skills add Tiramisu-wwh/quality-gate-skills --skill prd-gatekeeper
npx skills add Tiramisu-wwh/quality-gate-skills --skill security-prd-gatekeeper
npx skills add Tiramisu-wwh/quality-gate-skills --skill test-plan-xmind-generator
npx skills add Tiramisu-wwh/quality-gate-skills --skill testcase-generator
npx skills add Tiramisu-wwh/quality-gate-skills --skill company-security-code-review
npx skills add Tiramisu-wwh/quality-gate-skills --skill apifox-tests
```

## Notes

- `apifox-tests/env/*.env` 已改成占位符，安装后需要自行填写 Apifox 访问令牌和环境 ID。
- 这些 skills 以 Codex / Claude 类 agent 工作流为目标，部分内容默认依赖本地 Python、Node.js、Excel 模板和相关工具链。
