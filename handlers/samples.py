import time
import re
import datetime

from loader import dp, types, bot, connect_bd, keyboard, sample_state, FSMContext, other_commands
from filters.filter_commands import isPrivate, isUser


@dp.message_handler(isUser(), isPrivate(), commands=['edit_samples'], state="*")
async def edit_samples(message: types.Message):
  chat, first_name, username, user_id = message.chat.id, message.from_user.first_name or '', message.from_user.username and f"@{message.from_user.username}" or "", str(message.from_user.id)

  t, m = await keyboard.get_samples()
  await bot.send_message(chat, t, reply_markup=m)
  await sample_state.set_manager.set()

@dp.callback_query_handler(isPrivate(), state=sample_state.set_manager)
async def callback_data(message: types.CallbackQuery, state: FSMContext):
  chat, message_id = str(message.message.chat.id), message.message.message_id
  d = message.data.split(":")

  if d[0] == 'add_new':
    msg = await bot.send_message(chat, 'Отправьте текст шаблона', parse_mode='html')
    await other_commands.set_trash(msg)
    await state.update_data(message_id=message_id)
    await sample_state.new_sample.set()

  if d[0] == 'select':
    t, m = await keyboard.get_samples(sample_id=d[1])
    await bot.edit_message_text(t, chat, message_id, reply_markup=m)
    await sample_state.set_manager.set()

  if d[0] == 'del':
    await connect_bd.mongo_conn.db.samples.delete_one({'id': d[1]})
    t, m = await keyboard.get_samples()
    await bot.edit_message_text(t, chat, message_id, reply_markup=m)
    await sample_state.set_manager.set()

  if d[0] == 'edit':
    sample = await connect_bd.mongo_conn.db.samples.find_one({'id': d[1]})
    msg = await bot.send_message(chat, f'Отправьте изменённый текст шаблона: <code>{sample["text"]}</code>', parse_mode='html')
    await other_commands.set_trash(msg)
    await state.update_data(message_id=message_id, sample_id=d[1])
    await sample_state.edit_sample.set()

  if d[0] == 'new_buttons':
    msg = await bot.send_message(chat, 'Напишите текст кнопок. Пример:\n<code>Кнопка1 - https://ya.ru | Кнопка2 - https://google.com\nКнопка 3 - https://test.ru</code>', parse_mode='html')
    await other_commands.set_trash(msg)
    await state.update_data(message_id=message_id, sample_id=d[1])
    await sample_state.new_button.set()


@dp.message_handler(isPrivate(), state=sample_state.new_sample)
async def new_sample(message: types.Message, state: FSMContext):
  chat, first_name, username, user_id = message.chat.id, message.from_user.first_name or '', message.from_user.username and f"@{message.from_user.username}" or "", str(message.from_user.id)
  sample_text = message.text.strip()
  user_data = await state.get_data()
  id = str(int(time.time()))

  await connect_bd.mongo_conn.db.samples.insert_one({'id': id, 'text': sample_text, 'date': datetime.datetime.now()})
  t, m = await keyboard.get_samples()
  await bot.edit_message_text(t, chat, user_data['message_id'], reply_markup=m)

  await other_commands.set_trash(message, chat=chat)
  await sample_state.set_manager.set()

@dp.message_handler(isPrivate(), state=sample_state.edit_sample)
async def edit_sample(message: types.Message, state: FSMContext):
  chat, first_name, username, user_id = message.chat.id, message.from_user.first_name or '', message.from_user.username and f"@{message.from_user.username}" or "", str(message.from_user.id)
  sample_text = message.text.strip()
  user_data = await state.get_data()

  await connect_bd.mongo_conn.db.samples.update_one({'id': user_data['sample_id']}, {'$set': {'text': sample_text}})
  t, m = await keyboard.get_samples(sample_id=user_data['sample_id'])
  await bot.edit_message_text(t, chat, user_data['message_id'], reply_markup=m)

  await other_commands.set_trash(message, chat=chat)
  await sample_state.set_manager.set()


@dp.message_handler(isPrivate(), state=sample_state.new_button)
async def new_button(message: types.Message, state: FSMContext):
  chat, fullname, username, user_id = message.chat.id, message.from_user.full_name, message.from_user.username and f"@{message.from_user.username}" or "", str(
    message.from_user.id)
  butt = message.text
  user_data = await state.get_data()

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

    await connect_bd.mongo_conn.db.samples.update_one({'id': user_data['sample_id']}, {'$set': {'buttons': buttons, 'max_rows': max_rows}})
  else:
    await connect_bd.mongo_conn.db.samples.update_one({'id': user_data['sample_id']},
      {'$set': {'buttons': [], 'max_rows': 1}})

  t, m = await keyboard.get_samples(sample_id=user_data['sample_id'])
  await bot.edit_message_text(t, chat, user_data['message_id'], reply_markup=m)

  await other_commands.set_trash(message, chat=chat)
  await sample_state.set_manager.set()