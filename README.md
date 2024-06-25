# autodl-keeper
2024-06(🚧施工中) autodl自动续签 防止实例过期释放 

# 快速开始

## 克隆项目
```shell
git clone https://github.com/turbo-duck/autodl-keeper
cd autodl-keeper
````

![](./images/01.png)


## 新建配置
```shell
vim .env
```

写入内容为: 
- Authorization 为你的 Cookie
- MIN_DAY 为小于这个值则进行 开机-关机 的操作

```shell
Authorization=
MIN_DAY=7
```

## 获取Authorization
(这一块后续看是否可以自动化起来)
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


## 启动方案1: 本地启动

```shell
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
或者
```shell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
![](./images/04.png)

启动服务
```shell
nohup python main.py &
```

## 查看日志
```shell
tail -f nohup.out
```

可以观察到，已经续费了。
![](./images/05.png)


========================= 🚧 后续还在施工 ======================
## 启动方案2: 容器启动

## 拉取镜像
```shell
docker pull 
```

## 启动镜像
```shell
docker run -it -d -e 

```


# 详细内容
# env
```text
Authorization=
MIN_DAY=7
```

# requirements
```text
import os
from dotenv import load_dotenv
import requests
import json
import time
import logging
from datetime import datetime
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
```

# core code
```python
def open_machine(instance_uuid: str = None):
    if not instance_uuid:
        return False
    url = "https://www.autodl.com/api/v1/instance/power_on"
    body = {
        "instance_uuid": str(instance_uuid),
        "payload": "non_gpu"
    }
    response = requests.post(url=url, headers=headers, data=json.dumps(body))
    json_data = response.json()
    logging.info(f"uuid: {instance_uuid}, open")
    if json_data['code'] == "Success":
        return True
    return False
```

```python
def close_machine(instance_uuid: str = None):
    if not instance_uuid:
        return False
    url = "https://www.autodl.com/api/v1/instance/power_off"
    body = {
        "instance_uuid": str(instance_uuid)
    }
    response = requests.post(url=url, headers=headers, data=json.dumps(body))
    json_data = response.json()
    logging.info(f"uuid: {instance_uuid}, close")
    if json_data['code'] == "Success":
        return True
    return False
```

# Build By Dockerfile
```text
docker build -t autodl-keeper .
```

# Run By Docker
```text
docker run -d --env-file .env autodl-keeper
```
