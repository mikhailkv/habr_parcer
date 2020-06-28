from tortoise import Tortoise

from settings import DB_URL


async def init_db():
    await Tortoise.init(db_url=DB_URL, modules={"models": ["__main__"]})
    await Tortoise.generate_schemas()
    # await Tortoise.close_connections()
