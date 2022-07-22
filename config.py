import os

from dotenv import load_dotenv

load_dotenv()

KICKEX_PUB_KEY = os.getenv('KICKEX_PUB_KEY')
KICKEX_PR_KEY = os.getenv('KICKEX_PR_KEY')
KICKEX_PASSWORD = os.getenv('KICKEX_PASSWORD')

if not all([
    KICKEX_PUB_KEY,
    KICKEX_PR_KEY,
    KICKEX_PASSWORD,
]):
    raise Exception('You have to create .env and insert keys like .env.example')
