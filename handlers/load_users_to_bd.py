import asyncio
import aiohttp
import json
import re

from filters.filter_commands import isPrivate
from loader import dp, types, bot, bot_token, FSMContext, connect_bd

@dp.message_handler(isPrivate(), content_types='document', state="*")
async def get_files(message: types.document, state: FSMContext):
  if len(re.findall(r'^users.json$', message.document.file_name)) > 0:
    chat = str(message.chat.id)
    file_id = message.document.file_id
    f = await bot.get_file(file_id)
    async with aiohttp.ClientSession() as session:
      res = await session.get(f'https://api.telegram.org/file/bot{bot_token}/{f.file_path}')
      json_acc = json.loads(await res.text())

      users_bd = []
      async for user in connect_bd.mongo_conn.db.users.find():
        users_bd.append(user['user_id'])

      doc = []
      for user in json_acc:
        user_id = str(user['user_id'])
        if user_id not in users_bd:
          user['user_id'] = user_id
          user['fullname'] = user['first_name']
          doc.append(user)

      if doc:
        if len(doc) < 2:
          await connect_bd.mongo_conn.db.users.insert_one(doc[0])
        else:
          await connect_bd.mongo_conn.db.users.insert_many(doc)
      await bot.send_message(chat, f'Импорт юзеров сделан, импортировано {len(doc)} юзеров')