# Java 审计信号

优先关注：

- 入口：`@RestController`、`@Controller`、`@RequestMapping`
- 鉴权：`@PreAuthorize`、`@Secured`、`SecurityContextHolder`
- 文件：`MultipartFile`、`ZipInputStream`、`new File(...)`
- 外部请求：`RestTemplate`、`WebClient`、`HttpClient`
- 命令：`Runtime.getRuntime().exec`、`ProcessBuilder`
- 随机数：`SecureRandom`、`new Random`、`Math.random`
- 会话：`Cookie`、`ResponseCookie`
- 异常：`printStackTrace()`、`e.getMessage()`

重点问题：

- SQL 注入：字符串拼接 SQL、`executeQuery(... + ...)`
- 路径穿越：文件路径拼接用户输入，缺少 `normalize()` / `startsWith()`
- XXE：XML 解析器未关闭外部实体
- 反序列化：`ObjectInputStream`、`XMLDecoder`
- SSRF：用户可控 URL 进入 `RestTemplate` / `WebClient`
