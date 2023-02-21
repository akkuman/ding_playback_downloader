import re
import asyncio
import aiofiles
from mitmproxy import http
from mitmproxy import ctx
import httpx
from playwright.async_api import async_playwright

# chrome.exe 的地址
__EXECUTABLE_PATH__  = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
# 线程数
__THREAD__ = 4


# 下载m3u8格式的视频
async def download_m3u8(m3u8_url, store_path):
    async with httpx.AsyncClient() as client:
        resp = await client.get(m3u8_url)
        file_line = resp.text.split("\n")
        if file_line[0] != "#EXTM3U":
            raise BaseException(u"非M3U8的链接")
        ts_links = []
        for line in file_line:
            if line.startswith("#"):
                continue
            ts_links.append(f'{m3u8_url.rsplit("/", 1)[0]}/{line}')
        ctx.log.info(f'共有 {len(ts_links)} 个分片将被下载，线程数为 {__THREAD__}')
        sem = asyncio.Semaphore(__THREAD__)
        for index, ts_link in enumerate(ts_links):
            async with sem:
                ctx.log.info(f'开始下载第 {index+1} 个分片...')
                res = await client.get(ts_link)
                async with aiofiles.open(store_path, 'ab') as f:
                    await f.write(res.content)
                    await f.flush()
                ctx.log.info(f'第 {index+1} 个分片下载完成')
    ctx.log.info(f'已经下载完成: {store_path}')


async def handle(route):
    response = await route.fetch()
    resp_json = await response.json()
    url = resp_json['openLiveDetailModel']['playbackUrl']
    title = resp_json['openLiveDetailModel']['title']
    uid = resp_json['openLiveDetailModel']['uuid']
    ctx.log.info(f'获取到视频链接: [{title}](f{url})')
    asyncio.get_running_loop().create_task(download_m3u8(url, f'{uid}.ts'))
    await route.abort()

class Ding:
    def __init__(self, live_uuid: str):
        self.live_uuid = live_uuid
    
    async def process(self):
        url = f'https://login.dingtalk.com/oauth2/auth?client_id=dingavo6at488jbofmjs&response_type=code&scope=openid&redirect_uri=https%3A%2F%2Flv.dingtalk.com%2Fsso%2Flogin%3Fcontinue%3Dhttps%253A%252F%252Fh5.dingtalk.com%252Fgroup-live-share%252Findex.htm%253Ftype%253D2%2526liveFromType%253D6%2526liveUuid%253D{self.live_uuid}%2526bizType%253Ddingtalk%2526dd_nav_bgcolor%253DFF2C2D2F%2523%252Funion'
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
            await page.wait_for_selector('text=服务异常', timeout=0)


async def request(flow: http.HTTPFlow) -> None:
    if not flow.request.path.startswith('/group-live-share/index.htm'):
        return
    live_uuid = flow.request.query.get('liveUuid')
    ctx.log.info(f'获取到liveUuid: {live_uuid}')
    d = Ding(live_uuid)
    await d.process()
