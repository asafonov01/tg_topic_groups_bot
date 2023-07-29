from loader import dp, types, bot, welcome_state, FSMContext, connect_bd, keyboard, exceptions, other_commands
from filters.filter_commands import isPrivate, isUser
import re

async def editor_welcome(chat, message_id=None):
  welcome_data = await connect_bd.mongo_conn.db.welcome.find_one({'admin': True})
  buttons = welcome_data.get('buttons') or []
  message_id = message_id or welcome_data['message_id']

  m = await keyboard.get_buttons_welcome(welcome_data, buttons)
  msg = None
  if welcome_data.get('photo') and welcome_data.get('video') == '':
    if message_id:
      try:
        await bot.edit_message_caption(
          types.InputMediaPhoto(media=welcome_data['photo'], caption=welcome_data.get('text') or None, parse_mode='html'),
          chat, message_id, reply_markup=m)
      except:
        try:
          await bot.delete_message(chat, message_id)
        except:
          pass
        msg = await bot.send_photo(chat, photo=welcome_data['photo'], caption=welcome_data.get('text') or None, reply_markup=m,
          parse_mode='html')

    else:
      msg = await bot.send_photo(chat, photo=welcome_data['photo'], caption=welcome_data.get('text') or None, reply_markup=m,
        parse_mode='html')

  if welcome_data.get('video') and welcome_data.get('photo') == '':
    if message_id:
      try:
        await bot.edit_message_media(
          types.InputMediaVideo(media=welcome_data['video'], caption=welcome_data.get('text') or None, parse_mode='html'),
          chat, message_id, reply_markup=m)
      except:
        try:
          await bot.delete_message(chat, message_id)
        except:
          pass
        msg = await bot.send_video(chat, video=welcome_data['video'], caption=welcome_data.get('text') or None, reply_markup=m,
          parse_mode='html')
    else:
      msg = await bot.send_video(chat, video=welcome_data['video'], caption=welcome_data.get('text') or None, reply_markup=m,
        parse_mode='html')


  if welcome_data.get('photo') == '' and welcome_data.get('video') == '':
    try:
      await bot.edit_message_text(welcome_data['text'], chat, message_id, reply_markup=m, parse_mode='html',
        disable_web_page_preview=True)
    except exceptions.MessageNotModified:
      pass
    except Exception as e:
      try:
        await bot.delete_message(chat, message_id)
      except:
        pass
      msg = await bot.send_message(chat, welcome_data['text'], reply_markup=m, parse_mode='HTML',
        disable_web_page_preview=True)

  if msg:
    await connect_bd.mongo_conn.db.welcome.update_one({'admin': True}, {'$set': {'message_id': msg.message_id}})

@dp.message_handler(isUser(), isPrivate(), commands=['edit_welcome'], state="*")
async def edit_welcome(message: types.Message):
  chat, first_name, username, user_id = message.chat.id, message.from_user.first_name or '', message.from_user.username and f"@{message.from_user.username}" or "", str(message.from_user.id)

  welcome_data = await connect_bd.mongo_conn.db.welcome.find_one({'admin': True})
  if not welcome_data:
    welcome_data = {'admin': True, 'max_rows': 2, 'message_id': 0, 'text': '', 'photo': '', 'video': '', 'buttons': []}
    await connect_bd.mongo_conn.db.welcome.insert_one(welcome_data)

  if welcome_data['text'] == '':
    msg = await bot.send_message(chat, 'Начните писать текст, отправлять фото или видео', parse_mode='html')
  else:
    await editor_welcome(chat, message_id=message.message_id)

  await welcome_state.edit_content.set()

@dp.message_handler(isPrivate(), content_types=types.ContentType.ANY, state=welcome_state.edit_content)
async def get_content(message: types.Message, state: FSMContext):
  chat, fullname, username, user_id = message.chat.id, message.from_user.full_name, message.from_user.username and f"@{message.from_user.username}" or "", str(
    message.from_user.id)

  try:
    obj = {}
    if message.text or message.caption:
      text = message.html_text
      obj['text'] = text
    else:
      text = ''

    if text:
      if '/' == text[0]:
        await bot.send_message(chat, 'Вышел с режима редактирования, отправьте ещё раз команду')
        await state.reset_state(with_data=False)
        return False

    photo, video = '', ''
    if 'photo' in message:
      photo = message.photo[0].file_id
    if 'video' in message:
      video = message.video.file_id
    if 'animation' in message:
      video = message.animation.file_id

    await other_commands.set_trash(message, chat=chat)
    if photo or video:
      if photo:
        obj['photo'] = photo
        obj['video'] = ''

      if video:
        obj['video'] = video
        obj['photo'] = ''

      if text:
        obj['text'] = text

    await connect_bd.mongo_conn.db.welcome.update_one({'admin': True}, {'$set': obj})
    await editor_welcome(chat)
  except Exception as e:
    print(e)


@dp.callback_query_handler(isPrivate(), state=welcome_state.edit_content)
async def callback_data(message: types.CallbackQuery, state: FSMContext):
  chat, message_id = str(message.message.chat.id), message.message.message_id
  d = message.data.split(":")

  if d[0] == 'new_buttons':
    msg = await bot.send_message(chat, 'Напишите текст кнопок. Пример:\n<code>Кнопка1 - https://ya.ru | Кнопка2 - https://google.com\nКнопка 3 - https://test.ru</code>', parse_mode='html')
    await other_commands.set_trash(msg)
    await state.update_data(message_id=message_id)
    await welcome_state.new_button.set()

  if d[0] == 'del_photo' or d[0] == 'del_video':
    if d[0] == 'del_photo':
      await connect_bd.mongo_conn.db.welcome.update_one({'admin': True}, {'$set': {'photo': ''}})
    else:
      await connect_bd.mongo_conn.db.welcome.update_one({'admin': True}, {'$set': {'video': ''}})

    await editor_welcome(chat)
    await welcome_state.edit_content.set()


@dp.message_handler(isPrivate(), state=welcome_state.new_button)
async def new_button(message: types.Message, state: FSMContext):
  chat, fullname, username, user_id = message.chat.id, message.from_user.full_name, message.from_user.username and f"@{message.from_user.username}" or "", str(
    message.from_user.id)
  butt = message.text

  if 'нет' != message.text.strip().lower():
    rows = butt.split("\n")
    max_rows, buttons = 1, []
    for row in rows:
      if '|' in row:
        row_buttons = row.split('|')
        if len(row_buttons) > max_rows:
          max_rows = len(row_buttons)
        for button_info in row_buttons:
          text, url = button_info.split('-', maxsplit=1)
          if re.findall(
                  r'^((ftp|http|https):\/\/)?(www\.)?([A-Za-zА-Яа-я0-9]{1}[A-Za-zА-Яа-я0-9\-]*\.?)*\.{1}[A-Za-zА-Яа-я0-9-]{2,8}(\/([\w#!:.?+=&%@!\-\/])*)?',
                  url.strip()):
            buttons.append({'text': text.strip(), 'url': url.strip()})
          else:
            await bot.send_message(chat,
              f'Не могу добавить кнопку: <code>{button_info}</code>, не верный формат у ссылки', parse_mode='html')

      else:
        text, url = row.split('-', maxsplit=1)
        if re.findall(
                r'^((ftp|http|https):\/\/)?(www\.)?([A-Za-zА-Яа-я0-9]{1}[A-Za-zА-Яа-я0-9\-]*\.?)*\.{1}[A-Za-zА-Яа-я0-9-]{2,8}(\/([\w#!:.?+=&%@!\-\/])*)?',
                url.strip()):
          buttons.append({'text': text.strip(), 'url': url.strip()})
        else:
          await bot.send_message(chat,
            f'Не могу добавить кнопку, не верный формат у ссылки', parse_mode='html')

    await connect_bd.mongo_conn.db.welcome.update_one({'admin': True}, {'$set': {'buttons': buttons, 'max_rows': max_rows}})
  else:
    await connect_bd.mongo_conn.db.welcome.update_one({'admin': True}, {'$set': {'buttons': [], 'max_rows': 1}})

  await editor_welcome(chat)
  await other_commands.set_trash(message, chat=chat)
  await welcome_state.edit_content.set()