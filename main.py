import os
from dotenv import load_dotenv
import requests
import json
import time
import logging
from datetime import datetime
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler


load_dotenv()
authorization = os.getenv('Authorization')
min_day = os.getenv('MIN_DAY')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

headers = {
    "Authorization": authorization,
    "Content-Type": "application/json;charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


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
    logger.info(f"uuid: {instance_uuid}, open")
    logger.info(f"{instance_uuid} response: {json_data}")
    if json_data['code'] == "Success":
        return True
    return False


def close_machine(instance_uuid: str = None):
    if not instance_uuid:
        return False
    url = "https://www.autodl.com/api/v1/instance/power_off"
    body = {
        "instance_uuid": str(instance_uuid)
    }
    response = requests.post(url=url, headers=headers, data=json.dumps(body))
    json_data = response.json()
    logger.info(f"uuid: {instance_uuid}, close")
    logger.info(f"{instance_uuid} response: {json_data}")
    if json_data['code'] == "Success":
        return True
    return False


def check_instance(page: int = 1):
    url = "https://www.autodl.com/api/v1/instance"
    body = {
        "date_from": "",
        "date_to": "",
        "page_index": page,
        "page_size": 100,
        "status": [],
        "charge_type": []
    }
    response = requests.post(url=url, headers=headers, data=json.dumps(body))
    json_data = response.json()
    if json_data['code'] == "Success":
        data_list = json_data['data']['list']
        for each_data in data_list:
            uuid = each_data.get('uuid', '')
            if uuid == "":
                return
            machine_alias = each_data.get('machine_alias', '')
            region_name = each_data.get('region_name', '')
            status = each_data.get('status', '')
            status_at = each_data.get('status_at', '')
            phone = each_data.get('phone', '')

            status_at_time = datetime.fromisoformat(status_at)
            current_date = datetime.now(pytz.timezone('Asia/Shanghai'))
            date_difference = current_date - status_at_time
            date_difference_day = date_difference.days
            logger.info(f"now: {current_date.strftime('%Y-%m-%d %H:%M:%S')}, "
                         f"phone: {phone}, name: {region_name} {machine_alias} {uuid}, "
                         f"status: {status}, date_diff: {date_difference_day}天")
            # 小于1天
            if date_difference_day >= int(min_day):
                logger.info(f"准备续费: {uuid}")
                # 续费逻辑
                open_machine(uuid)
                time.sleep(60)
                close_machine(uuid)
                time.sleep(5)
            else:
                logger.info(f"等待下次扫描: {uuid}")
                # 不作操作
                pass
    else:
        return


def main():
    if not authorization:
        logger.error("Authorization is None !")
        exit(-1)
    logger.info(f"now: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}")
    check_instance()


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'interval', hours=1)
    try:
        # 启动调度器
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("KeyboardInterrupt Or SystemExit")
