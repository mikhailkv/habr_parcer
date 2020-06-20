import os

INTERVAL = int(os.getenv('INTERVAL', 5))
FILE_PATH = os.getenv('FILE_PATH', 'posts.json')

DB_DATABASE = os.getenv('FILE_PATH', 'database')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5444')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_USER = os.getenv('FDB_USER', 'user')

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
CHUNK_SIZE = 2
