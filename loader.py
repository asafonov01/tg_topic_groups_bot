
from aiogram import Bot, Dispatcher, types, exceptions
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.mongo import MongoStorage

from mongodb import connect_bd
from utils import other_commands, mailing_state, keyboard, throttling, welcome_state, sample_state
from data.config import bot_token, conf, topic_chat_id

isChat = filters.IDFilter

bot = Bot(token=bot_token, parse_mode='html')

dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(throttling.ThrottlingMiddleware())
rate_limit = throttling.rate_limit