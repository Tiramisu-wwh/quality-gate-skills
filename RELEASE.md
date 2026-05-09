# Public Repo Release Notes

## 发布前检查

1. 确认新增内容属于可公开分发范围。
2. 检查 `skills/<skill-name>/SKILL.md` frontmatter 仅包含：
   - `name`
   - `description`
3. 检查是否残留以下内容：
   - 本机绝对路径
   - access token、cookie、环境密钥
   - 公司内部链接、内部系统名、条款编号、专有模板
4. 删除 `node_modules`、`__pycache__`、测试输出、报告文件。

## 验证建议

- Python skill：`python3 -m py_compile <script>`
- 有单测的 skill：`python3 -m unittest discover -s tests -v`
- Node skill：在对应目录执行 `npm ci` 后跑最小脚本检查
- `SKILL.md`：确认 `description` 只描述触发条件，不写执行流程

## 发布步骤

1. 更新 `README.md` 中的技能列表、安装方式、准备说明。
2. 提交代码：

```bash
git add .
git commit -m "feat: update public skills"
```

3. 打版本 tag：

```bash
git tag v0.1.0
```

4. 推送分支和 tag：

```bash
git push origin main
git push origin v0.1.0
```
