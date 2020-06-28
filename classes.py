import asyncio
import json
import logging
import re
import sys

from json import JSONDecodeError
from typing import List, Iterator, Dict

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from tortoise import Tortoise

from models import Post
from settings import DB_URL, FILE_PATH, CHUNK_SIZE, URL_PATTERN

log = logging.getLogger()


class Handler:
    """
    Базовый класс обработчиков
    """
    def __init__(self):
        self.log = log


class DBManager:

    """
    Manager отвечающий за работу с БД
    """

    @classmethod
    async def init(cls) -> None:
        await Tortoise.init(db_url=DB_URL, modules={"models": ["__main__"]})
        await Tortoise.generate_schemas()
        await Tortoise.close_connections()

    @classmethod
    async def connect(cls) -> None:
        await Tortoise.init(db_url=DB_URL, modules={"models": ["__main__"]})

    @classmethod
    async def close(cls) -> None:
        await Tortoise.close_connections()


class DBHandler(Handler, DBManager):

    def __init__(self):
        Handler.__init__(self)
        self.model = Post

    async def check_urls(self, data: List) -> Iterator:
        """
        Метод для проверки наличия обработанных url
        """
        exist_urls = await self.model.filter(url__in=data).values_list('url', flat=True)
        return (url for url in data if url not in exist_urls)

    async def commit_data(self, data: List):
        """
        Метод для сохранения данных в БД
        """
        await self.model.bulk_create([Post(**el) for el in data])
        return True


class FileHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.data = None

    def read_file(self):
        try:
            with open(FILE_PATH, 'r') as file_obj:
               self._validate_data(json.load(file_obj))
        except (JSONDecodeError, FileNotFoundError) as e:
            sys.stdout.write(f'{str(e)}\n')

    def __iter__(self):
        for el in range(0, len(self.data), CHUNK_SIZE):
            yield self.data[el: el + CHUNK_SIZE]

    def _validate_data(self, data: List):
        """
        Метод для валидации url
        """
        self.data = [el for el in data if re.findall(URL_PATTERN, el)]


class ParseHandler(Handler):

    async def parse_html(self, data: List) -> List[Dict]:
        """
        Метод для прасинга html
        """
        res = []
        for url, html in data:
            if not html:
                self.log.info('Not html data')
                continue
            soup = BeautifulSoup(html, "html.parser")
            post_title = soup.find('span', {'class': 'post__title-text'})
            post_text = soup.find('div', {'class': 'post__text post__text-html post__text_v1'})
            res.append({'title': post_title, 'text': post_text, 'url': url})
        return res


class FetchHandler(Handler):

    async def fetch(self, session: ClientSession, url: str):
        async with session.get(url) as response:
            return (url, await response.text()) if response.status == 200 else (url, None)

    async def fetch_all(self, data: List) -> Iterator:
        """
        Метод для получения html
        """
        async with ClientSession(loop=asyncio.get_event_loop()) as session:
            return await asyncio.gather(*(self.fetch(session, url) for url in data), return_exceptions=True)
