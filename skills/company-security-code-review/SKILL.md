---
name: company-security-code-review
description: Use when auditing Java, Node.js or TypeScript, or Python code against company security checklist and SS-006 requirements before release, security review, or left-shift security checks.
---

# 公司安全规范源码审计

把这个 skill 当成“智能体做语义审计”的技能，而不是单纯的多语言正则扫描器。

优先依靠智能体理解代码入口、鉴权边界、数据流、危险 sink 和已有缓解措施；再用脚本收集候选证据。不要把脚本的“未发现”直接当成“符合规范”。

## Start

1. 先读取 `references/company_security_requirements.md`。
2. 再读取 `references/agent_review_playbook.md`。
3. 识别代码主语言后，只加载相关参考：
   - Java：`references/java_review_signals.md`
   - Node.js / TypeScript：`references/node_ts_review_signals.md`
   - Python：`references/python_review_signals.md`
4. 只有在需要风险分级和证据标准时，再读 `references/detection_rules.md`。

## Review Workflow

1. 先圈定范围。
   - 识别控制器 / 路由 / 视图入口
   - 识别鉴权配置、过滤器、中间件、拦截器、guard、dependency
   - 识别上传下载、压缩包解析、XML 解析、反序列化、外部 HTTP 调用、日志、配置文件
   - 识别密码、token、session、cookie、验证码、资源 ID 读取路径

2. 先做预扫描收集线索。

```bash
python3 scripts/company_compliance_scan.py /path/to/project --format markdown
```

把这一步当成“候选问题列表”，不要直接当结论。

3. 再用 `rg` 缩小人工审计范围。

```bash
rg -n "GetMapping|RequestMapping|app\\.(get|post|put|delete)|router\\.(get|post|put|delete)|@app\\.(get|post)|@router\\.(get|post)|PreAuthorize|Secured|RolesAllowed|MultipartFile|multer|UploadFile|request\\.files|ZipInputStream|zipfile|ObjectInputStream|pickle\\.load|yaml\\.load|DocumentBuilderFactory|requests\\.|axios\\.|fetch\\(|Runtime\\.getRuntime|child_process|subprocess\\.|exec\\(|sendRedirect|redirect\\(|res\\.redirect|new Cookie|ResponseCookie|res\\.cookie|set_cookie|printStackTrace|error\\.message|MD5|SHA-1|DES|RC4|Math\\.random|new Random|SecureRandom|secrets\\.|crypto\\.randomBytes|findById\\(|SELECT |INSERT |UPDATE |DELETE " /path/to/project
```

4. 对高风险路径做语义追踪。
   - 追输入来源：参数、请求体、Header、Cookie、Multipart、配置项、外部响应
   - 追缓解措施：服务端校验、白名单、编码、鉴权、事务回滚、统一异常处理、文件隔离、强加密、安全随机数
   - 追危险 sink：SQL、命令执行、重定向、外部请求、文件路径、日志、异常返回、模板回显、下载接口、对象查询
   - 判断缓解措施是否真的落在当前链路上，而不是“项目里某处存在”

5. 按条款输出结论。
   - `符合`：源码里有正向证据，且该条款可以通过源码直接证明
   - `不符合`：源码里有明确反例或关键控制缺失
   - `需人工确认`：依赖网关、部署、运行配置、产品规则、测试数据或跨系统联调
   - `不适用`：该系统没有该类功能

6. 明确边界。
   - 不要仅凭“没搜到问题”就写 `符合`
   - 不要把 HTTPS、TLS、端口收敛、KMS、MFA、验证码频率、密码过期策略这类运行态 / 管理态要求写成“已符合”
   - 对越权、ID 可遍历、文件下载等问题，要结合具体业务对象和鉴权路径再下结论

## Language Coverage

- Java / Spring
- Node.js / TypeScript
  - Express / Koa / Nest 风格代码优先
- Python
  - Flask / FastAPI / Django 风格代码优先

支持程度分层：

- 通用条款映射：三种语言都适用
- 预扫描脚本：三种语言都支持基础高风险线索提取
- 语义审计：以智能体理解业务链路为主，不依赖脚本穷尽所有语言细节

## What To Look For

- 敏感信息：GET 参数、硬编码、明文日志、明文存储、过量返回字段
- 输入输出：服务端校验、输出编码、SQL 注入、XSS、SSRF、命令注入、URL 重定向、XXE
- 认证授权：入口认证、服务端鉴权、敏感接口二次校验、资源级访问控制
- 会话安全：Cookie `HttpOnly` / `Secure`、会话更新、token 随机性、会话 ID 是否出现在 URL / 日志
- 文件安全：类型白名单、大小校验、路径规范化、临时文件清理、zip 解压防护、下载鉴权
- 密码与加密：弱算法、弱随机数、口令存储方式、硬编码密钥、密钥配置方式
- 日志与异常：敏感信息脱敏、统一异常返回、禁止堆栈 / 组件版本 / 数据库结构泄露

## Output Requirements

输出至少包含：

- 业务结论：`通过` / `有条件通过` / `不通过`
- 高风险发现：文件、行号、攻击路径、修复建议、对应公司条款
- 条款矩阵：`符合 / 不符合 / 需人工确认 / 不适用`
- `需人工确认` 列表：明确说明为什么源码无法直接证明
- 残余风险：说明这次审计没有覆盖或无法完全证明的区域

优先使用 `assets/report_template.md` 的结构。

## Scripts

- `scripts/company_compliance_scan.py`
  - 首选的公司条款导向多语言预扫描器
  - 支持 Java、Node.js / TypeScript、Python
  - 输出“候选问题 + 条款映射 + 需人工确认项”

## Assets

- `assets/report_template.md`：公司安全规范审计报告模板
