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
            await page.wait_for_selector('#dingapp', timeout=120*1000)
        

class DingVideo:
    def __init__(self, live_uuid: str):
        self.live_uuid = live_uuid
        self.session = requests.Session()

    def get_login_code(self) -> str:
        '''获取登录code'''
        url = 'https://login.dingtalk.com/oauth2/local/generate_code'
        headers = {
            'referer': f'https://login.dingtalk.com/oauth2/challenge.htm?client_id=dingavo6at488jbofmjs&response_type=code&scope=openid&redirect_uri=https%3A%2F%2Flv.dingtalk.com%2Fsso%2Flogin%3Fcontinue%3Dhttps%253A%252F%252Fh5.dingtalk.com%252Fgroup-live-share%252Findex.htm%253Ftype%253D2%2526liveFromType%253D6%2526liveUuid%253D{self.live_uuid}%2526bizType%253Ddingtalk%2526dd_nav_bgcolor%253DFF2C2D2F%2523%252Funion'
        }
        data = {
            'client_id': 'dingavo6at488jbofmjs',
            'response_type': 'code',
            'scope': 'openid',
            'redirect_uri': f'https://lv.dingtalk.com/sso/login?continue=https%3A%2F%2Fh5.dingtalk.com%2Fgroup-live-share%2Findex.htm%3Ftype%3D2%26liveFromType%3D6%26liveUuid%3D{self.live_uuid}%26bizType%3Ddingtalk%26dd_nav_bgcolor%3DFF2C2D2F%23%2Funion',
        }
        resp = self.session.post(url, headers=headers, data=data)
        result_url = resp.json()['result']
        result_url = urlparse(result_url)
        code = parse_qs(result_url.query)['code'][0]
        ctx.log.info(f'code: {code}')
        return code

    def query_login_user(self, code: str) -> dict:
        '''获取登录的用户列表'''
        url = 'https://login.dingtalk.com/oauth2/local/query_user'
        headers = {
            'referer': f'https://login.dingtalk.com/oauth2/challenge.htm?client_id=dingavo6at488jbofmjs&response_type=code&scope=openid&redirect_uri=https%3A%2F%2Flv.dingtalk.com%2Fsso%2Flogin%3Fcontinue%3Dhttps%253A%252F%252Fh5.dingtalk.com%252Fgroup-live-share%252Findex.htm%253Ftype%253D2%2526liveFromType%253D6%2526liveUuid%253D{self.live_uuid}%2526bizType%253Ddingtalk%2526dd_nav_bgcolor%253DFF2C2D2F%2523%252Funion'
        }
        data = {
            'client_id': 'dingavo6at488jbofmjs',
            'response_type': 'code',
            'scope': 'openid',
            'redirect_uri': f'https://lv.dingtalk.com/sso/login?continue=https%3A%2F%2Fh5.dingtalk.com%2Fgroup-live-share%2Findex.htm%3Ftype%3D2%26liveFromType%3D6%26liveUuid%3D{self.live_uuid}%26bizType%3Ddingtalk%26dd_nav_bgcolor%3DFF2C2D2F%23%2Funion',
            'code': code,
        }
        resp = self.session.post(url, headers=headers, data=data)
        ctx.log.info(f'query_login_user: {resp.text}')
        user_info = resp.json()['result']
        return user_info

    def login_ding(self, code: str, user_info: dict):
        url = 'https://login.dingtalk.com/oauth2/local/login'
        headers = {
            'referer': f'https://login.dingtalk.com/oauth2/challenge.htm?client_id=dingavo6at488jbofmjs&response_type=code&scope=openid&redirect_uri=https%3A%2F%2Flv.dingtalk.com%2Fsso%2Flogin%3Fcontinue%3Dhttps%253A%252F%252Fh5.dingtalk.com%252Fgroup-live-share%252Findex.htm%253Ftype%253D2%2526liveFromType%253D6%2526liveUuid%253D{self.live_uuid}%2526bizType%253Ddingtalk%2526dd_nav_bgcolor%253DFF2C2D2F%2523%252Funion'
        }
        data = {
            'client_id': 'dingavo6at488jbofmjs',
            'response_type': 'code',
            'scope': 'openid',
            'redirect_uri': f'https://lv.dingtalk.com/sso/login?continue=https%3A%2F%2Fh5.dingtalk.com%2Fgroup-live-share%2Findex.htm%3Ftype%3D2%26liveFromType%3D6%26liveUuid%3D{self.live_uuid}%26bizType%3Ddingtalk%26dd_nav_bgcolor%3DFF2C2D2F%23%2Funion',
            'code': code,
            'uidCipher': user_info['uidCipher'],
            'stayLogin': 'false',
        }
        resp = requests.post(url, headers=headers, data=data)
        ctx.log.info(resp.text)

    def confirm_auth(self, code: str) -> str:
        url = 'https://login.dingtalk.com/oauth2/confirm_auth'
        headers = {
            'referer': f'https://login.dingtalk.com/oauth2/challenge.htm?client_id=dingavo6at488jbofmjs&response_type=code&scope=openid&redirect_uri=https%3A%2F%2Flv.dingtalk.com%2Fsso%2Flogin%3Fcontinue%3Dhttps%253A%252F%252Fh5.dingtalk.com%252Fgroup-live-share%252Findex.htm%253Ftype%253D2%2526liveFromType%253D6%2526liveUuid%253D{self.live_uuid}%2526bizType%253Ddingtalk%2526dd_nav_bgcolor%253DFF2C2D2F%2523%252Funion'
        }
        data = {
            'client_id': 'dingavo6at488jbofmjs',
            'response_type': 'code',
            'scope': 'openid',
            'redirect_uri': f'https://lv.dingtalk.com/sso/login?continue=https%3A%2F%2Fh5.dingtalk.com%2Fgroup-live-share%2Findex.htm%3Ftype%3D2%26liveFromType%3D6%26liveUuid%3D{self.live_uuid}%26bizType%3Ddingtalk%26dd_nav_bgcolor%3DFF2C2D2F%23%2Funion',
            'corpId': '',
            'secondaryValidationResult': '',
        }
        resp = requests.post(url, headers=headers, data=data)
        result = resp.json()['result']
        redirect_url = result['url']
        return redirect_url

    def sso_login(self, redirect_url: str) -> str:
        resp = requests.get(redirect_url, allow_redirects=False)
        pc_session_id = resp.cookies['PC_SESSION']
        ctx.log.info(f'PC_SESSION: {pc_session_id}')
        return pc_session_id

    def get_m3u8_url(self, pc_session_id: str) -> dict:
        url = f'https://lv.dingtalk.com/getOpenLiveInfo?liveUuid={self.live_uuid}&unifyLiveType=2&token=&pcCode='
        cookies = {
            'PC_SESSION': pc_session_id,
        }
        resp = requests.get(url, cookies=cookies)
        ctx.log.info(resp.text)
        return {
            'm3u8_url': resp.json()['openLiveDetailModel']['playbackUrl'],
            'title': resp.json()['openLiveDetailModel']['title'],
            'uuid': self.live_uuid,
        }

    def process(self):
        code = self.get_login_code()
        user_info = self.query_login_user(code)
        self.login_ding(code, user_info)
        redirect_url = self.confirm_auth(code)
        pc_session_id = self.sso_login(redirect_url)
        m3u8_info = self.get_m3u8_url(pc_session_id)
        ctx.log.info(str(m3u8_info))

async def _process(live_uuid: str):
    d = Ding(live_uuid)
    await d.process()

async def request(flow: http.HTTPFlow) -> None:
    if not flow.request.path.startswith('/group-live-share/index.htm'):
        return
    live_uuid = flow.request.query.get('liveUuid')
    ctx.log.info(f'获取到liveUuid: {live_uuid}')
    await _process(live_uuid)
