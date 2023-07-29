from aiogram import Dispatcher
from .filter_commands import isUser, isPrivate, isMessageButtons

def setup(dp: Dispatcher):
  dp.filters_factory.bind(isUser)