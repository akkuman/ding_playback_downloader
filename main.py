import re
from urllib.parse import urlparse
from urllib.parse import parse_qs
from mitmproxy import http
from mitmproxy import ctx
import requests
from playwright.async_api import async_playwright

# chrome.exe 的地址
__EXECUTABLE_PATH__  = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"


async def handle(route):
    response = await route.fetch()
    resp_json = await response.json()
    ctx.log.info(resp_json)
    url = resp_json['openLiveDetailModel']['playbackUrl']
    title = resp_json['openLiveDetailModel']['title']
    ctx.log.info(f'获取到视频链接: [f{title}](f{url})')
    await route.abort()

class Ding:
    def __init__(self, live_uuid: str):
        self.live_uuid = live_uuid
        self.session = requests.Session()
    
    async def process(self):
        url = f'https://login.dingtalk.com/oauth2/auth?client_id=dingavo6at488jbofmjs&response_type=code&scope=openid&redirect_uri=https%3A%2F%2Flv.dingtalk.com%2Fsso%2Flogin%3Fcontinue%3Dhttps%253A%252F%252Fh5.dingtalk.com%252Fgroup-live-share%252Findex.htm%253Ftype%253D2%2526liveFromType%253D6%2526liveUuid%253D{self.live_uuid}%2526bizType%253Ddingtalk%2526dd_nav_bgcolor%253DFF2C2D2F%2523%252Funion'
        pc_session_id = None
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                # 指定本机google客户端exe的路径
                executable_path=__EXECUTABLE_PATH__,
                # 设置不是无头模式
                headless=False,
                slow_mo=10,
                #跳过检测
                args=['--disable-blink-features=AutomationControlled']
            )
            context = await browser.new_context()
            page = await context.new_page()
            await page.route(re.compile(r"getOpenLiveInfo"), handle) 
            await page.goto(url)
            await page.wait_for_selector('#dingapp', timeout=0)


async def _process(live_uuid: str):
    d = Ding(live_uuid)
    await d.process()

async def request(flow: http.HTTPFlow) -> None:
    if not flow.request.path.startswith('/group-live-share/index.htm'):
        return
    live_uuid = flow.request.query.get('liveUuid')
    ctx.log.info(f'获取到liveUuid: {live_uuid}')
    await _process(live_uuid)
