import asyncio
import json
import time
import sys
import schedule

from typing import List, Generator
from aiohttp import ClientSession
from json import JSONDecodeError
from bs4 import BeautifulSoup
from tortoise import Tortoise, run_async

from models import Post
from settings import DB_URL, FILE_PATH, CHUNK_SIZE, CRON


async def fetch(session: ClientSession, url: str):
    async with session.get(url) as response:
        return await response.text() if response.status == 200 else None


async def fetch_all(urls: List, loop: asyncio.events) -> Generator:
    async with ClientSession(loop=loop) as session:
        results = await asyncio.gather(*(fetch(session, url) for url in urls), return_exceptions=True)
        return results


def get_urls() -> List:
    urls = []
    try:
        with open(FILE_PATH, 'r') as file_obj:
            urls = json.load(file_obj)
    except JSONDecodeError as e:
        sys.stdout.write(f'{str(e)}\n')
    except FileNotFoundError as e:
        sys.stdout.write(f'{str(e)}\n')
    return urls


def parse_html(html_data: Generator):
    for html in html_data:
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        post_title = soup.find('span', {'class': 'post__title-text'})
        post_text = soup.find('div', {'class': 'post__text post__text-html post__text_v1'})
        yield {'title': post_title, 'text': post_text}


async def commit_data(html_data: Generator):
    await Tortoise.init(db_url=DB_URL, modules={"models": ["__main__"]})
    await Tortoise.generate_schemas()
    post_data_to_save = []
    for i, data in enumerate(parse_html(html_data), start=1):

        post_data_to_save.append(
            Post(**data)
        )
        if i % CHUNK_SIZE:
            await Post.bulk_create(post_data_to_save)
            post_data_to_save = []
    await Post.bulk_create(post_data_to_save)
    post_count = await Post.all().count()
    sys.stdout.write("Post count: {count}\n".format(count=post_count))


def run_task():
    sys.stdout.write("Run task\n")
    urls = get_urls()
    loop = asyncio.get_event_loop()
    html_data = loop.run_until_complete(fetch_all(urls, loop))
    run_async(commit_data(html_data))
    sys.stdout.write("Task done\n")


if __name__ == '__main__':
    sys.stdout.write("Start service\n")
    from crontab import CronTab
    cron = CronTab(crontab=CRON)
    schedule.every(cron.next(default_utc=True)).seconds.do(run_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

