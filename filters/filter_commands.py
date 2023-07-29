from time import time
import re
from datetime import datetime
from aiogram.dispatcher.filters import BoundFilter

from loader import types, conf, connect_bd


class isUser(BoundFilter):
  async def check(self, message: types.Message):
    chat, user_id = 'message' in message and message.message.chat.id or message.chat.id, str(message.from_user.id)
    fullname = message.from_user.full_name
    username = message.from_user.username or ''
    user = await connect_bd.mongo_conn.db.users.find_one({'user_id': user_id})

    if user:
      if user.get('is_banned') == True:
        return False

    if not user:
      obj = {'user_id': user_id, 'fullname': fullname, 'username': username, 'created': datetime.now(), 'history': [], 'is_banned': False}
      await connect_bd.mongo_conn.db.users.insert_one(obj)
    else:
      if user['username'] != username or user['fullname'] != fullname:
        await connect_bd.mongo_conn.db.users.update_one({'user_id': user_id}, {'$set': {'username': username, 'fullname': fullname}})

    return True

class isPrivate(BoundFilter):
  async def check(self, message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in conf['admin']['id']:
      return True
    return False

class isMessageButtons(BoundFilter):
  async def check(self, message: types.Message):
    d = message.data.split(":")
    if d[0] in ['block_user', 'samples_variant', 'exit_select_samples', 'select_send']:
      return True
    return False