# Node.js / TypeScript 审计信号

优先关注：

- 入口：`app.get/post`、`router.get/post`、Nest `@Controller` / `@Get`
- 鉴权：中间件、`@UseGuards`、权限装饰器、`passport`、自定义 `auth`
- 文件：`multer`、`req.files`、`fs.*`、`path.join`
- 外部请求：`axios`、`fetch`、`got`
- 命令：`child_process.exec`、`execSync`、`spawn`
- 随机数：`crypto.randomBytes`、`crypto.randomUUID`、`Math.random`
- 会话：`res.cookie`、session middleware
- 日志：`console.log`、`logger.*`

重点问题：

- SQL 注入：模板字符串或拼接进入 `.query(...)`
- 命令注入：用户输入进入 `exec(...)`
- 开放重定向：`res.redirect(req.query.next)`
- 路径穿越：`sendFile` / `fs.readFile` 直接使用 `req.params` / `req.query`
- SSRF：用户输入进入 `axios.get(url)` / `fetch(url)`
- 弱随机数：token、验证码、重置码使用 `Math.random`
