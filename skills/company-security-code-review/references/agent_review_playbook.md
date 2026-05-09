# Agent 审计 Playbook

## 目录

- 1. 先做什么
- 2. 预扫描怎么用
- 3. 高信号搜索模式
- 4. 怎么做语义审计
- 5. 怎么避免误报
- 6. 最终报告怎么写

## 1. 先做什么

1. 先读 `company_security_requirements.md`，明确哪些条款能通过源码直接证明。
2. 再圈代码范围：
   - `controller` / `api` / `router` / `views`
   - `security` / `auth` / `login` / `middleware`
   - `filter` / `interceptor` / `guard` / `dependency`
   - `upload` / `download` / `file`
   - `client` / `http` / `resttemplate` / `axios` / `requests`
   - `config` / `properties` / `yml` / `.env`
   - `log` / `audit`

## 2. 预扫描怎么用

首选：

```bash
python3 scripts/company_compliance_scan.py /path/to/project --format markdown --output company-security-review.md
```

用法原则：

- 把输出当成候选证据，不要当最终结论
- 先看 `critical` / `high`
- 再回到源码确认真实利用路径和缓解措施
- 如果脚本没命中，不等于代码符合

## 3. 高信号搜索模式

### 3.1 Java

```bash
rg -n "@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping)|@PreAuthorize|@Secured|@RolesAllowed|MultipartFile|ZipInputStream|DocumentBuilderFactory|ObjectInputStream|Runtime\\.getRuntime|ProcessBuilder|sendRedirect|RestTemplate|WebClient|new Cookie|ResponseCookie|printStackTrace|e\\.getMessage|SecureRandom|findById\\(" /path/to/project
```

### 3.2 Node.js / TypeScript

```bash
rg -n "app\\.(get|post|put|delete)|router\\.(get|post|put|delete)|@Controller|@Get|@Post|@UseGuards|multer|req\\.(query|params|body|files)|axios\\.|fetch\\(|got\\(|child_process|exec\\(|spawn\\(|res\\.redirect|res\\.cookie|Math\\.random|crypto\\.randomBytes|sequelize\\.query|\\.query\\(" /path/to/project
```

### 3.3 Python

```bash
rg -n "@app\\.(get|post|put|delete)|@router\\.(get|post|put|delete)|request\\.(args|form|json|files)|UploadFile|FileResponse|send_file|requests\\.|httpx\\.|subprocess\\.|os\\.system|pickle\\.load|yaml\\.load|set_cookie|hashlib\\.(md5|sha1)|random\\.|secrets\\.|objects\\.get\\(" /path/to/project
```

### 3.4 重点看什么

- 管理类接口、导出接口、删除 / 更新 / 审批 / 下载接口
- 路径参数或查询参数中的 `id`
- 鉴权只在前端做、后端没做对象级校验的情况
- 用户输入有没有直接到 SQL、命令、URL、响应体、模板、外部请求
- 有无服务端校验、白名单、编码或转义

## 4. 怎么做语义审计

对每个高风险候选点，至少回答下面 5 个问题：

1. 输入从哪里来？
   - 用户输入、Header、Cookie、文件名、配置、外部响应、定时任务参数

2. 中间有没有真正生效的控制？
   - 服务端校验
   - 白名单
   - 转义 / 编码
   - 鉴权 / 二次校验
   - 路径规范化
   - 安全随机数
   - 安全算法 / 安全配置

3. 最终 sink 是什么？
   - SQL、命令、URL、日志、模板、文件系统、外部请求、下载响应

4. 影响面是什么？
   - 数据泄露
   - 越权
   - 任意文件访问
   - 远程命令执行
   - 账号接管
   - 敏感信息暴露

5. 这条公司规范能不能仅靠源码证明？
   - 能：给 `符合` 或 `不符合`
   - 不能：给 `需人工确认`

## 5. 怎么避免误报

- 不要因为项目里出现了安全框架，就默认当前链路已被保护
- 不要因为同一个文件里有参数化查询或校验器，就默认所有路径都安全
- 不要把“接口路径里有 `/admin`”直接等同于高风险；先确认是否真的执行敏感操作
- 不要把“未搜到敏感字段”直接写成“符合脱敏要求”
- 不要把依赖配置中心、网关、KMS、Nginx、WAF 的控制写成源码已符合

## 6. 最终报告怎么写

最终报告至少包含：

- 审计范围与假设
- 总体门禁结论：`通过` / `有条件通过` / `不通过`
- 明确不符合项：文件、行号、攻击路径、条款、修复建议
- 已观察到的正向控制
- `需人工确认` 项及其原因
- 残余风险与后续建议

建议按 `assets/report_template.md` 的结构输出。
