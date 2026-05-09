# Python 审计信号

优先关注：

- 入口：Flask / FastAPI / Django 路由、视图、APIView
- 鉴权：装饰器、permission class、dependency、middleware
- 文件：`request.files`、`UploadFile`、`send_file`、`FileResponse`、`zipfile`
- 外部请求：`requests`、`httpx`
- 命令：`subprocess.*`、`os.system`
- 随机数：`secrets`、`os.urandom`、`random`
- 会话：`set_cookie`、session、JWT
- 反序列化：`pickle.load(s)`、`yaml.load`

重点问题：

- SQL 注入：`cursor.execute(f"...")`、字符串格式化 SQL
- 命令注入：用户输入进入 `subprocess` 且 `shell=True`
- 路径穿越：`open(base + user_input)`、`send_file(user_path)`
- SSRF：用户输入进入 `requests.get(url)`
- 弱随机数：token、验证码、重置码使用 `random`
- 不安全反序列化：`pickle.loads`、`yaml.load`
