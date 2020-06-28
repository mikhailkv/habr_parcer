import asyncio
import logging
import sys
from json import JSONDecodeError

from crontab import CronTab

from classes import (
    FileHandler,
    ParseHandler,
    FetchHandler,
    DBHandler
)
from exceptions import ImportWorkerError
from models import Post
from settings import CRON, DEBUG


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')
log = logging.getLogger('main')


class ImportWorker:
    def __init__(self):
        self.cron_obj = CronTab(crontab=CRON)
        self.db_handler = DBHandler()
        self.file_handler = FileHandler()
        self.parse_hadler = ParseHandler()
        self.fetch_handler = FetchHandler()

    @property
    def next_run(self) -> float:
        """
        Метод для получения времени в секундах до следующего запуска
        """
        return self.cron_obj.next(default_utc=True)

    @property
    def chain_method(self):
        return [
            self.db_handler.check_urls,
            self.fetch_handler.fetch_all,
            self.parse_hadler.parse_html,
            self.db_handler.commit_data,
        ]

    @classmethod
    async def start(cls) -> 'ImportWorker':
        self = cls()
        await self.scheduler
        return self

    async def execute_method(self, method, **kwargs):
        try:
            res = await asyncio.wait_for(method(**kwargs), timeout=self.next_run)
        except asyncio.TimeoutError:
            log.error(f'Timeout in method: {method.__name__}')
            # если не успели выполнить таску до начала
            # следующей, закрываем соединение рейзим исключение
            await asyncio.create_task(DBHandler.close())
            raise ImportWorkerError
        return res

    async def run_task(self):
        try:
            log.info('Run task')
            # Читаем файл
            self.file_handler.read_file()
            # Подключаемся к БД
            await asyncio.create_task(DBHandler.connect())
            for chuck_urls in self.file_handler:
                # Получаем для обработки часть urls
                data, done = chuck_urls, True
                for method in self.chain_method:
                    # по цепочке получаем методы обработчика
                    # результат выполнения метода передаем в следующий
                    data = await self.execute_method(method, **{'data': data})
        except (ImportWorkerError, FileNotFoundError, JSONDecodeError):
            log.error('task fail')
        else:
            # Закрываем соединение
            await asyncio.create_task(DBHandler.close())
            log.info('done task')

    @property
    async def scheduler(self):
        while True:
            await self.run_task()
            await asyncio.sleep(self.next_run)


if __name__ == '__main__':
    log.info('Run service')
    loop = asyncio.get_event_loop()
    log.info("Init db")
    log.info(f"Scheduler {CRON}")
    try:
        # Подключаемся к БД, проверям схему, создаем таблицы если их нет
        loop.run_until_complete(DBHandler.init())
        # Запускаем worker
        worker = loop.run_until_complete(ImportWorker.start())
        loop.run_forever()
    except ConnectionRefusedError as e:
        log.error(f'{str(e)}')

