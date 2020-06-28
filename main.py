import asyncio
import json
import sys
from collections import OrderedDict

from typing import List, Generator
from aiohttp import ClientSession
from json import JSONDecodeError
from bs4 import BeautifulSoup
from crontab import CronTab

from models import Post
from settings import FILE_PATH, CRON

from utils import init_db


class DBManager:

    @classmethod
    async def check_urls(cls, urls):
        exist_urls = await Post.filter(url__in=urls).values_list('url', flat=True)
        return (url for url in urls if url not in exist_urls)

    @classmethod
    async def commit_data(cls, parse_data: Generator):
        await Post.bulk_create([Post(**data) for data in parse_data])
        post_count = await Post.all().count()
        sys.stdout.write("Post count: {count}\n".format(count=post_count))
        return post_count


class ImportWorker:
    def __init__(self):
        self.cron_obj = CronTab(crontab=CRON)

    @property
    def next_run(self):
        return self.cron_obj.next(default_utc=True)

    @property
    def chain_method(self):
        return OrderedDict([
            (DBManager.check_urls, 'urls'),
            (self.fetch_all, 'urls'),
            (parse_html, 'html_data'),
            (DBManager.commit_data, 'parse_data')
        ])

    @classmethod
    async def start(cls) -> 'ImportWorker':
        self = cls()

        await self.scheduler
        return self

    async def fetch(self, session: ClientSession, url: str):
        async with session.get(url) as response:
            return (url, await response.text()) if response.status == 200 else (url, None)

    async def fetch_all(self, urls: List) -> Generator:
        async with ClientSession(loop=asyncio.get_event_loop()) as session:
            results = await asyncio.gather(*(self.fetch(session, url) for url in urls), return_exceptions=True)
            return results

    async def execute_func(self, method, **kwargs):
        print(kwargs)
        try:
            res = await asyncio.wait_for(method(**kwargs), timeout=self.next_run)
        except asyncio.TimeoutError:
            print('TimeOut!!!!')
            res = None
        return res

    async def run_task(self):
        print('run task')
        data = get_urls()
        for method, args_name in self.chain_method.items():
            kwargs = {args_name: data}
            data = await self.execute_func(method, **kwargs)
            if data is None:
                break
        print('done task')

    @property
    async def scheduler(self):
        while True:
            await self.run_task()
            await asyncio.sleep(self.next_run)


def get_urls() -> List:
    urls = []
    try:
        with open(FILE_PATH, 'r') as file_obj:
            urls = json.load(file_obj)
    except (JSONDecodeError, FileNotFoundError) as e:
        sys.stdout.write(f'{str(e)}\n')
    return urls


async def parse_html(html_data: Generator):
    data = []
    for url, html in html_data:
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        post_title = soup.find('span', {'class': 'post__title-text'})
        post_text = soup.find('div', {'class': 'post__text post__text-html post__text_v1'})
        data.append({'title': post_title, 'text': post_text, 'url': url})
    return data


if __name__ == '__main__':
    sys.stdout.write("Run service\n")
    loop = asyncio.get_event_loop()
    sys.stdout.write("Init db\n")
    loop.run_until_complete(init_db())
    worker = loop.run_until_complete(ImportWorker.start())
    loop.run_forever()

