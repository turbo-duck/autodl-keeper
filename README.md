# autodl-keeper

AutoDL 自动续签工具，用于通过“开机 -> 等待 -> 关机”的方式延长实例存活时间，避免实例过期释放。

## 当前状态

- 当前主线版本已经支持两种鉴权方式：优先使用已有 `Authorization`，失效时回退到 Playwright 自动登录获取 token。
- 当前实现为单文件脚本，主要逻辑集中在 `main.py`。
- 程序启动后会先立即执行一次检查，然后按固定 1 小时间隔继续巡检。
- 目前仓库没有自动化测试，也没有独立的登录模块，登录逻辑直接写在 `main.py` 中。

## 功能概览

- 支持通过 `Authorization` 直接访问 AutoDL 接口
- 支持通过 Playwright 自动登录网页并捕获 token
- 支持 `--headed` 观察浏览器自动登录过程
- 自动扫描实例列表，筛选达到阈值的实例并执行续签动作
- 支持本地运行和基础 Docker 运行

## 项目结构

```text
autodl-keeper/
├── .env.template
├── Dockerfile
├── README.md
├── main.py
├── requirements.txt
└── images/
```

## 运行要求

- Python 3.10 或更高版本
- 能访问 AutoDL 官网
- 如果需要自动登录，必须安装 Playwright 依赖和 Chromium 浏览器

说明：

- 如果你只打算使用现成的 `Authorization`，不触发自动登录时可以暂时不安装 Playwright
- 当程序需要回退到自动登录时，才会检查 `playwright` 和 Chromium 是否可用

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/turbo-duck/autodl-keeper
cd autodl-keeper
```

### 2. 创建配置文件

```bash
cp .env.template .env
```

`.env` 当前支持以下配置：

```env
Authorization=
AUTODL_PHONE=
AUTODL_PASSWORD=
AUTODL_LOGIN_RETRIES=3
AUTODL_LOGIN_TIMEOUT_MS=15000
AUTODL_POST_LOGIN_WAIT_SECONDS=8
MIN_DAY=7
```

字段说明：

- `Authorization`：已有 token，可选；如果有效会优先使用
- `AUTODL_PHONE`：AutoDL 登录手机号
- `AUTODL_PASSWORD`：AutoDL 登录密码
- `AUTODL_LOGIN_RETRIES`：Playwright 登录重试次数
- `AUTODL_LOGIN_TIMEOUT_MS`：单次登录超时时间，单位毫秒
- `AUTODL_POST_LOGIN_WAIT_SECONDS`：点击登录后额外等待 token 的秒数
- `MIN_DAY`：实例运行天数达到该值后触发续签动作

## 鉴权方式

### 方式 1：手动填写 Authorization

1. 登录 AutoDL 官网
2. 打开浏览器开发者工具
3. 在 Network 面板中找到任意 `/api/v1/instance` 或其他 AutoDL 接口请求
4. 复制请求头中的 `Authorization`
5. 填入 `.env` 的 `Authorization`

相关示意图：

![](./images/02.png)

![](./images/03.png)

### 方式 2：Playwright 自动登录

当 `Authorization` 缺失或失效时，程序会尝试使用 `.env` 中的 `AUTODL_PHONE` 和 `AUTODL_PASSWORD` 自动登录网页，并从登录响应中提取 token。

说明：

- 默认使用无头浏览器
- 可以通过 `--headed` 打开可视浏览器观察登录过程
- 如果页面卡住、出现验证码或多次超时，程序会退出并输出错误信息
- 当前登录实现位于 `main.py`，并没有单独的 `login.py`

## 本地运行

### 1. 安装依赖

```bash
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 安装 Chromium

如果你要使用 Playwright 自动登录，需要额外安装浏览器：

```bash
playwright install chromium
```

### 3. 启动程序

```bash
python main.py
```

程序行为：

- 启动后立即执行一次检查
- 如果实例运行天数大于等于 `MIN_DAY`，则执行开机、等待 60 秒、关机、等待 5 秒
- 完成首轮后，按每 1 小时执行一次继续运行

如果你想观察浏览器自动登录过程：

```bash
python main.py --headed
```

后台运行示例：

```bash
nohup python main.py > nohup.out 2>&1 &
tail -f nohup.out
```

效果示意：

![](./images/04.png)

![](./images/05.png)

## Docker 运行

### 构建镜像

```bash
docker build -t autodl-keeper .
```

说明：

- 当前镜像构建会自动安装 Playwright Chromium 及其运行依赖
- 构建时间会比纯 Python 镜像更长一些，但容器内自动登录会更稳定

### 启动容器

```bash
docker run -d \
  --name autodl-keeper \
  --env-file .env \
  autodl-keeper
```

### 查看日志

```bash
docker logs -f autodl-keeper
```

相关示意图：

![](./images/06.png)

![](./images/07.png)

## 当前实现细节

- 巡检间隔当前写死为 1 小时，没有环境变量开关
- 续签动作当前固定为开机等待 60 秒、关机等待 5 秒
- 当前只扫描实例列表首页，单次最多处理 100 条记录
- 代码只保留了基础日志输出，没有统计持久化、Webhook、实例过滤等增强能力

## 已知限制

- 当前仓库没有自动化测试
- 自动登录依赖 Playwright 和 Chromium，环境未准备好时只能使用现成 `Authorization`
- 如果容器环境缺少浏览器和系统依赖，Playwright 自动登录流程可能无法使用

## 变更记录

- 详细变更见 [CHANGELOG.md](./CHANGELOG.md)
- 当前版本发布说明见 [RELEASE_NOTES.md](./RELEASE_NOTES.md)

## 开发说明

如果你准备继续开发，这个版本更适合先做下面几类整理：

- 把登录、API 请求、续签逻辑从 `main.py` 中拆分出来
- 给固定参数增加环境变量配置
- 增加最基本的测试和错误恢复逻辑
- 为 Docker 场景补齐 Playwright 浏览器依赖

## 截图

![](./images/01.png)

![](./images/08.png)
