import time
import re
from datetime import datetime, timedelta
from loader import types, connect_bd

class aio_keyboard:


  async def get_buttons_edit_mail(self, user_data, buttons, select_button='', mailing=False, preview=False,
    not_url=False):
    max_rows = user_data.get('max_rows') or 2
    keyboard = types.InlineKeyboardMarkup(row_width=max_rows)
    arr = []

    if buttons and not not_url:
      for butt in buttons:
        arr.append({'text': butt['text'], 'url': butt['url']})

    keyboard.add(*arr)

    if not preview:
      keyboard.add({'text': '➖➖➖➖➖➖➖➖➖➖➖➖', 'callback_data': 'edit_command'})
      keyboard.add({'text': 'Добавить кнопки', 'callback_data': f'new_buttons'})

      keyboard.add(*[
        {'text': user_data.get('photo') and 'Удалить 📷' or '', 'callback_data': f'del_photo'},
        {'text': user_data.get('video') and 'Удалить 📹' or '', 'callback_data': f'del_video'},
        {'text': 'Удалить всё' or '', 'callback_data': f'del_all'}
      ])

      keyboard.add(*[
        {'text': 'Предпросмотр', 'callback_data': f'preview_mode'},
        {'text': 'Сделать рассылку', 'callback_data': f'start_mailing'}
      ])
      keyboard.add({'text': 'Админ рассылка', 'callback_data': f'start_admin_mail'})
    else:
      if not mailing:
        keyboard.add({'text': '📝 Режим редактора', 'callback_data': 'edit_mode'})

    return keyboard

  async def get_buttons_welcome(self, user_data, buttons):
    max_rows = user_data['max_rows']
    keyboard = types.InlineKeyboardMarkup(row_width=max_rows)
    arr = []

    if buttons:
      for butt in buttons:
        arr.append({'text': butt['text'], 'url': butt['url']})

    keyboard.add(*arr)

    keyboard.add({'text': '➖➖➖➖➖➖➖➖➖➖➖➖', 'callback_data': 'edit_command'})
    keyboard.add({'text': 'Добавить кнопки', 'callback_data': f'new_buttons'})

    keyboard.add(*[
      {'text': user_data.get('photo') and 'Удалить 📷' or '', 'callback_data': f'del_photo'},
      {'text': user_data.get('video') and 'Удалить 📹' or '', 'callback_data': f'del_video'}
    ])

    return keyboard

  async def welcome_buttons(self, max_rows, buttons):
    keyboard = types.InlineKeyboardMarkup(row_width=max_rows)
    arr = []

    for butt in buttons:
      arr.append({'text': butt['text'], 'url': butt['url']})

    keyboard.add(*arr)
    return keyboard

  async def get_samples(self, sample_id='', visible_samples=True, settings=True, dop_settings=False, user='', sample=False, topic_id=''):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    t = 'Список шаблонов для быстрого ответа:'

    if visible_samples:
      async for sample in connect_bd.mongo_conn.db.samples.find():
        if sample_id == sample['id']:
          butts = ""
          if sample.get('buttons'):
            butts, i = '\n\nКнопки:', 1
            for butt in sample['buttons']:
              butts += f'\n{i}. <a href="{butt["url"]}">{butt["text"]}</a>'
              i += 1

          t = f'Текст шаблона: <code>{sample["text"]}</code>\n\nДата создания: {sample["date"]}{butts}'
          keyboard.add({'text': "✅ "+sample['text'], 'callback_data': f'selected:{sample["id"]}'})
        else:
          u, type_u = '', 'select'
          if user:
            u, type_u = user['user_id']+":", 'select_send'
          keyboard.add({'text': sample['text'], 'callback_data': f'{type_u}:{sample and u or ""}{sample["id"]}:{topic_id}'})

      if sample and not settings and not dop_settings:
        keyboard.add({'text': '❌', 'callback_data': f'exit_select_samples:{user["user_id"]}'})

    if settings:
      if sample_id:
        keyboard.add(*[
          {'text': 'Удалить', 'callback_data': f'del:{sample_id}'},
          {'text': 'Изменить', 'callback_data': f'edit:{sample_id}'}
        ])
        keyboard.add({'text': 'Добавить кнопки', 'callback_data': f'new_buttons:{sample_id}'})
      keyboard.add({'text': 'Добавить новый', 'callback_data': f'add_new'})

    if dop_settings:
      keyboard.add(*[
        {'text': '↩️', 'callback_data': f'samples_variant:{user["user_id"]}'}
      ])

    return t, keyboard

  async def get_button_for_sample(self, sample):
    if sample.get('buttons'):
      keyboard = types.InlineKeyboardMarkup(row_width=sample['max_rows'])
      arr = []

      for butt in sample['buttons']:
        arr.append({'text': butt['text'], 'url': butt['url']})

      keyboard.add(*arr)
      return keyboard

  async def get_admin_buttons(self, user):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add({'text': user.get('is_banned') and '🔓 Разблокировать' or '🔒 Заблокировать', 'callback_data': f'block_user:{user["user_id"]}'})
    return keyboard