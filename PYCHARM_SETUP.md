# PyCharm 创建、运行与验证说明

## 1. 直接打开已经生成的项目

1. 启动 PyCharm。
2. 点击 `File -> Open`。
3. 选择项目根目录 `ecommerce-agent`，不要只选择 `app` 文件夹。
4. 等待 PyCharm 完成文件索引。

项目根目录的判断方法：它里面应当直接包含 `app`、`tests`、`requirements.txt` 和 `README.md`。

## 2. 选择项目解释器

1. 打开 `File -> Settings -> Python -> Interpreter`。
2. 展开解释器列表，点击 `Add Interpreter -> Add Local Interpreter`。
3. 选择已有解释器，定位到：

   ```text
   项目目录\.venv\Scripts\python.exe
   ```

4. 确认后点击 `Apply -> OK`。

如果现有 `.venv` 在你的 PyCharm 中无效，可以新建一个 Virtualenv，再在 PyCharm 底部 Terminal 执行：

```powershell
python -m pip install -r requirements.txt
```

## 3. 理解第一批文件

```text
app/main.py                 创建 FastAPI 应用并挂载路由
app/api/routes/health.py    提供 GET /health 接口
app/core/config.py          从 .env 读取集中配置
.env                        本机真实配置，不应提交或分享
.env.example                可公开的配置字段示例
requirements.txt            项目所需 Python 包
tests/test_health.py        首页、健康检查和文档测试
pytest.ini                  pytest 的项目路径设置
```

Python Package 目录中的 `__init__.py` 用来告诉 Python：这个目录可以作为包导入。普通数据目录 `data` 和 `logs` 不需要它。

## 4. 建立 PyCharm 运行配置

1. 打开 `Run -> Edit Configurations`。
2. 点击左上角 `+`，选择 `Python`。
3. 名称填写 `Ecommerce Agent API`。
4. 运行目标选择 `Module name`。
5. Module name 填写 `uvicorn`。
6. Parameters 填写：

   ```text
   app.main:app --reload --host 127.0.0.1 --port 8000
   ```

7. Working directory 选择包含 `app` 和 `requirements.txt` 的项目根目录。
8. Python interpreter 选择本项目 `.venv` 中的 `python.exe`。
9. 点击 `Apply -> OK`。

`app.main:app` 分成三部分理解：

- 第一个 `app`：`app` 文件夹；
- `main`：`app/main.py` 文件；
- 最后一个 `app`：文件中的 `app = create_app()` 变量。

## 5. 启动和停止

在 PyCharm 右上角选择 `Ecommerce Agent API`，点击绿色三角形。正常输出应包含：

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete
```

也可以直接在 PyCharm Terminal 中启动：

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

停止时点击 Run 窗口的红色方块，或者在 Terminal 中按 `Ctrl+C`。

## 6. 浏览器验收

服务保持运行时依次访问：

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

验收结果：

- `/` 返回应用名称、版本和文档地址；
- `/health` 返回 `status: ok`；
- `/docs` 出现 Swagger UI，并能看到“首页”和“系统状态”两个分组。

## 7. 运行自动化测试

在 PyCharm Terminal 中执行：

```powershell
python -m pytest -q
```

应看到 3 个测试通过。测试分别检查：

1. 首页状态码和返回数据；
2. 健康检查状态码和返回数据；
3. OpenAPI 文档和 Swagger 页面是否能生成。

## 8. 常见问题

### `No module named fastapi`

当前解释器没有安装依赖。确认解释器指向项目 `.venv`，然后执行：

```powershell
python -m pip install -r requirements.txt
```

### `Could not import module app.main`

通常是 Working directory 选错了。它必须是项目根目录，而不是 `app` 目录。

### `Address already in use`

8000 端口已被占用。先停止旧服务，或者把运行参数中的端口改成 `8001`，再访问 `http://127.0.0.1:8001/docs`。

### 页面无法访问

确认 Run 窗口仍显示服务正在运行，并且访问的是 `http`，不是 `https`。

## 9. “本地运行”和“公网部署”的区别

当前方式是本地部署，只能在本机使用。它适合开发、学习、测试和面试演示。

项目全部功能完成后，再进行公网部署。届时通常需要云服务器，并增加 Docker、PostgreSQL、Redis 和 Nginx。现阶段不安装这些工具，避免同时引入过多问题。
