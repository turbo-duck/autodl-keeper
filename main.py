import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

import pytz
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


LOGIN_URL = "https://www.autodl.com/login"
PASSPORT_URL = "https://www.autodl.com/api/v1/passport"
INSTANCE_URL = "https://www.autodl.com/api/v1/instance"
POWER_ON_URL = "https://www.autodl.com/api/v1/instance/power_on"
POWER_OFF_URL = "https://www.autodl.com/api/v1/instance/power_off"
ASIA_SHANGHAI = pytz.timezone("Asia/Shanghai")
DEFAULT_LOGIN_TIMEOUT_MS = 15000
DEFAULT_LOGIN_RETRIES = 3
DEFAULT_POST_LOGIN_WAIT_SECONDS = 8
RUNTIME_AUTHORIZATION: Optional[str] = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


load_dotenv()


class AuthError(RuntimeError):
    pass


def build_headers(authorization: str) -> dict:
    return {
        "Authorization": authorization,
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    }


def alert_auth_failure(message: str) -> None:
    border = "=" * 72
    logger.error(border)
    logger.error("AUTODL TOKEN 获取失败")
    logger.error(message)
    logger.error(border)
    print(f"\n{border}\nAUTODL TOKEN 获取失败\n{message}\n{border}\n", file=sys.stderr)


def validate_authorization(authorization: str, request_timeout: int = 30) -> bool:
    if not authorization:
        return False

    body = {
        "date_from": "",
        "date_to": "",
        "page_index": 1,
        "page_size": 1,
        "status": [],
        "charge_type": [],
    }

    try:
        response = requests.post(
            url=INSTANCE_URL,
            headers=build_headers(authorization),
            json=body,
            timeout=request_timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Authorization 校验请求失败: %s", exc)
        return False

    return response.json().get("code") == "Success"


def run_single_login_attempt(
    phone: str,
    password: str,
    headed: bool,
    timeout_ms: int,
    post_login_wait_seconds: int,
) -> str:
    captured: dict[str, Optional[str]] = {"token": None}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        def handle_response(response) -> None:
            if PASSPORT_URL not in response.url:
                return

            try:
                payload = response.json()
            except Exception as exc:
                logger.warning("解析 passport 响应失败: %s", exc)
                return

            data = payload.get("data") or {}
            token = data.get("token")
            if token:
                captured["token"] = token

        page.on("response", handle_response)

        try:
            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")

            phone_input = page.locator('input[name="phone"]')
            password_input = page.locator('input[name="password"]')
            login_button = page.locator("button.el-button--primary").first

            phone_input.wait_for(state="visible")
            password_input.wait_for(state="visible")

            phone_input.fill("")
            phone_input.type(phone, delay=80)
            password_input.fill("")
            password_input.type(password, delay=80)

            with page.expect_response(
                lambda response: PASSPORT_URL in response.url,
                timeout=timeout_ms,
            ):
                login_button.click()

            if captured["token"]:
                return captured["token"]

            page.wait_for_timeout(post_login_wait_seconds * 1000)
            if captured["token"]:
                return captured["token"]

            raise AuthError("未在 passport 响应中捕获到 token，可能触发了验证码或页面未正常提交")
        except PlaywrightTimeoutError as exc:
            raise AuthError("页面加载或接口等待超时，可能是页面卡住或触发验证码") from exc
        finally:
            context.close()
            browser.close()


def fetch_token_via_playwright(
    phone: str,
    password: str,
    headed: bool,
    timeout_ms: int,
    max_retries: int,
    post_login_wait_seconds: int,
) -> str:
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        logger.info("开始通过 Playwright 获取 token，第 %s/%s 次尝试", attempt, max_retries)
        try:
            token = run_single_login_attempt(
                phone=phone,
                password=password,
                headed=headed,
                timeout_ms=timeout_ms,
                post_login_wait_seconds=post_login_wait_seconds,
            )
            logger.info("Playwright 登录成功，已捕获 token")
            return token
        except Exception as exc:
            last_error = exc
            logger.warning("Playwright 登录失败，第 %s 次尝试: %s", attempt, exc)
            time.sleep(min(attempt, 3))

    raise AuthError(f"多次尝试后仍无法获取 token: {last_error}")


class AutoDLClient:
    def __init__(
        self,
        authorization: str,
        min_day: int,
        request_timeout: int = 30,
    ):
        self.authorization = authorization
        self.min_day = min_day
        self.request_timeout = request_timeout
        self.session = requests.Session()

    def post_json(self, url: str, body: dict) -> dict:
        response = self.session.post(
            url=url,
            headers=build_headers(self.authorization),
            data=json.dumps(body),
            timeout=self.request_timeout,
        )
        response.raise_for_status()
        return response.json()

    def open_machine(self, instance_uuid: str) -> bool:
        body = {
            "instance_uuid": str(instance_uuid),
            "payload": "non_gpu",
        }
        json_data = self.post_json(POWER_ON_URL, body)
        logger.info("uuid: %s, open 机器开机", instance_uuid)
        logger.info("%s response: %s", instance_uuid, json_data)
        if json_data.get("code") == "Success":
            logger.info("uuid: %s, 机器开机成功", instance_uuid)
            return True
        return False

    def close_machine(self, instance_uuid: str) -> bool:
        body = {
            "instance_uuid": str(instance_uuid),
        }
        json_data = self.post_json(POWER_OFF_URL, body)
        logger.info("uuid: %s, close 机器关机", instance_uuid)
        logger.info("%s response: %s", instance_uuid, json_data)
        if json_data.get("code") == "Success":
            logger.info("uuid: %s, 机器关机成功", instance_uuid)
            return True
        return False

    def check_instance(self, page: int = 1) -> None:
        body = {
            "date_from": "",
            "date_to": "",
            "page_index": page,
            "page_size": 100,
            "status": [],
            "charge_type": [],
        }
        json_data = self.post_json(INSTANCE_URL, body)
        if json_data.get("code") != "Success":
            logger.error("扫描失败: %s", json_data)
            return

        data_list = json_data["data"]["list"]
        for each_data in data_list:
            uuid = each_data.get("uuid", "")
            if not uuid:
                continue

            machine_alias = each_data.get("machine_alias", "")
            region_name = each_data.get("region_name", "")
            status = each_data.get("status", "")
            status_at = each_data.get("status_at", "")
            phone = each_data.get("phone", "")

            status_at_time = datetime.fromisoformat(status_at)
            current_date = datetime.now(ASIA_SHANGHAI)
            date_difference = current_date - status_at_time
            date_difference_day = date_difference.days

            logger.info(
                "now: %s, phone: %s, name: %s %s %s, status: %s, date_diff: %s天",
                current_date.strftime("%Y-%m-%d %H:%M:%S"),
                phone,
                region_name,
                machine_alias,
                uuid,
                status,
                date_difference_day,
            )

            if date_difference_day >= self.min_day:
                logger.info("准备续费: %s", uuid)
                self.open_machine(uuid)
                time.sleep(60)
                self.close_machine(uuid)
                time.sleep(5)
            else:
                logger.info("等待下次扫描: %s", uuid)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AutoDL keeper")
    parser.add_argument(
        "--headed",
        action="store_true",
        help="使用有头模式启动 Playwright 浏览器",
    )
    return parser.parse_args()


def env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "")
    if not raw_value:
        return default
    return int(raw_value)


def resolve_authorization(headed: bool) -> str:
    global RUNTIME_AUTHORIZATION

    authorization = RUNTIME_AUTHORIZATION or os.getenv("Authorization", "").strip()
    if validate_authorization(authorization):
        logger.info("检测到可用的 Authorization，继续使用现有配置")
        RUNTIME_AUTHORIZATION = authorization
        return authorization

    phone = os.getenv("AUTODL_PHONE", "").strip()
    password = os.getenv("AUTODL_PASSWORD", "").strip()
    login_retries = env_int("AUTODL_LOGIN_RETRIES", DEFAULT_LOGIN_RETRIES)
    timeout_ms = env_int("AUTODL_LOGIN_TIMEOUT_MS", DEFAULT_LOGIN_TIMEOUT_MS)
    post_login_wait_seconds = env_int(
        "AUTODL_POST_LOGIN_WAIT_SECONDS",
        DEFAULT_POST_LOGIN_WAIT_SECONDS,
    )

    if not phone or not password:
        raise AuthError("Authorization 无效，且缺少 AUTODL_PHONE / AUTODL_PASSWORD 配置")

    logger.info("现有 Authorization 不可用，切换为 Playwright 登录")
    authorization = fetch_token_via_playwright(
        phone=phone,
        password=password,
        headed=headed,
        timeout_ms=timeout_ms,
        max_retries=login_retries,
        post_login_wait_seconds=post_login_wait_seconds,
    )
    RUNTIME_AUTHORIZATION = authorization
    return authorization


def create_client(headed: bool) -> AutoDLClient:
    min_day = env_int("MIN_DAY", 7)
    authorization = resolve_authorization(headed=headed)
    return AutoDLClient(
        authorization=authorization,
        min_day=min_day,
    )


def run_once(headed: bool) -> None:
    logger.info("now: %s", datetime.now(ASIA_SHANGHAI).strftime("%Y-%m-%d %H:%M:%S"))
    client = create_client(headed=headed)
    client.check_instance()


def main() -> None:
    args = parse_args()

    try:
        run_once(headed=args.headed)
    except AuthError as exc:
        alert_auth_failure(str(exc))
        raise SystemExit(1) from exc

    scheduler = BlockingScheduler()
    scheduler.add_job(run_once, "interval", hours=1, kwargs={"headed": args.headed})
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("KeyboardInterrupt Or SystemExit")


if __name__ == "__main__":
    main()
