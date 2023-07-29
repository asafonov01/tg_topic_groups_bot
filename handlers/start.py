from loader import dp, types, bot, connect_bd, keyboard
from filters.filter_commands import isUser

@dp.message_handler(isUser(), commands=['start'], state="*")
async def start(message: types.Message):
  chat, first_name, username, user_id = message.chat.id, message.from_user.first_name or '', message.from_user.username and f"@{message.from_user.username}" or "", str(message.from_user.id)

  welcome_data = await connect_bd.mongo_conn.db.welcome.find_one({'admin': True})
  if welcome_data:
    m = None
    if welcome_data['buttons']:
      m = await keyboard.welcome_buttons(welcome_data['max_rows'], welcome_data['buttons'])

    if welcome_data['photo']:
      await bot.send_photo(chat, photo=welcome_data['photo'], caption=welcome_data['text'], reply_markup=m)
    elif welcome_data['video']:
      await bot.send_video(chat, video=welcome_data['video'], caption=welcome_data['text'], reply_markup=m)
    else:
      await bot.send_message(chat, welcome_data['text'], reply_markup=m)
  else:
    await bot.send_message(chat, 'Добро пожаловать. Задайте интересующий вопрос и мы Вам ответим.')