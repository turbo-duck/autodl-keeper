# autodl-keeper
2024-06(🚧施工中) autodl自动续签 防止实例过期释放 

2024-07-20 已经测试一个月了 一切正常 可以正常续费

# 快速开始

## 克隆项目
```shell
git clone https://github.com/turbo-duck/autodl-keeper
cd autodl-keeper
````

![](./images/01.png)


## 新建配置
.env.template 为模板 你可以直接复制 或者 mv 修改名字
```shell
vim .env
```

写入内容为: 
- Authorization 为你的 token，可选
- AUTODL_PHONE / AUTODL_PASSWORD 为网页登录手机号和密码
- MIN_DAY 为小于这个值则进行 开机-关机 的操作

```shell
Authorization=
AUTODL_PHONE=
AUTODL_PASSWORD=
AUTODL_LOGIN_RETRIES=3
AUTODL_LOGIN_TIMEOUT_MS=15000
AUTODL_POST_LOGIN_WAIT_SECONDS=8
MIN_DAY=7
```

## 鉴权方式
当前支持两种方式，优先使用可用的 `Authorization`，失效时自动回退到 Playwright 登录取 token。

### 方式1: 手动填写 Authorization
- vim 新建 .env
- 打开你的 AutoDL网页 F12
- 刷新一下 随便找一个接口
- 找到 Request Headers 部分
- 取出 Authorization 对应的值
- 取出的值 Copy 到 .env 的Authorization
- wq 退出vim

![](./images/02.png)

填写结果如下
![](./images/03.png)

### 方式2: Playwright 自动登录
- 在 `.env` 中填写 `AUTODL_PHONE` 和 `AUTODL_PASSWORD`
- 如果页面偶发卡住或触发验证码，程序会自动重试
- 多次重试失败时，会在本地终端打印醒目的错误信息并退出
- 当前只实现桌面端自动化流程
- 登录相关实现已单独拆分到 `login.py`


## 启动方案1: 本地启动

```shell
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
或者
```shell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

安装 Playwright Chromium 浏览器
```shell
playwright install chromium
```
![](./images/04.png)

启动服务
```shell
nohup python main.py &
```

如果你想观察浏览器自动登录过程，可以改为：
```shell
python main.py --headed
```

## 查看日志
```shell
tail -f nohup.out
```

可以观察到，已经续费了。
![](./images/05.png)


## 启动方案2: 容器启动
你可以选择拉取现有镜像，或者自己打包。

**注意: 你需要查看 "新建配置" 的内容 需要配置一下 .env**

当前目录应该是这个样子:
```shell
.
├── Dockerfile
├── .env !注意这里是必须的!
├── .env.template
├── .git
├── .gitignore
├── LICENSE
├── main.py
├── nohup.out
├── README.md
└── requirements.txt
```

## 二选一: 拉取镜像
```shell
docker pull wdkang/autodl-keeper:v1.0
```
![](./images/08.png)

## 二选一: 打包镜像
```shell
docker build -t autodl-keeper .
```
![](./images/06.png)


## 启动镜像
```shell
docker run -d --env-file .env --name autodl-keeper autodl-keeper 
```
查看日志
```shell
docker logs -f autodl-keeper
```

![](./images/07.png)
