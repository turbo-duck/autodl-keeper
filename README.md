# autodl-keeper
2024-06(🚧施工中) autodl自动续签 防止实例过期释放 

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
docker run --env-file .env autodl-keeper
```
