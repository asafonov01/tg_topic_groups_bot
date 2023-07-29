import re

from loader import dp, types, bot, connect_bd, topic_chat_id, conf, isChat, keyboard
from filters.filter_commands import isPrivate, isUser
from utils.functions import Func

other_function = Func()


@dp.edited_message_handler(isUser(), isPrivate(), isChat(chat_id=topic_chat_id), content_types=types.ContentTypes.ANY, state="*")
async def edit_message_in_user(message: types.Message):
  chat, first_name, username, user_id = message.chat.id, message.from_user.first_name or '', message.from_user.username and f"@{message.from_user.username}" or "", str(message.from_user.id)

  if message.reply_to_message:
    if message.reply_to_message.forum_topic_created:
      photo, video = None, None
      if message.text != None:
        t = message.text
      else:
        try:
          t = message.caption or ''
          photo = message.photo[0].file_id
        except:
          t = message.caption
          try:
            video = message.video.file_id
          except:
            video = message.animation.file_id

      user_idd = re.findall(r'[(]([0-9]+)', message.reply_to_message.forum_topic_created.name)[0]
      is_user_topic = await connect_bd.mongo_conn.db.topics.find_one({'user_id': user_idd})
      if is_user_topic.get('admin_history'):
        if is_user_topic['admin_history'].get(str(message.message_id)):
          admin_content = is_user_topic['admin_history'][str(message.message_id)]
          admin_content['user_id'] = user_idd
          admin_content['text'] = t
          admin_content['photo'] = photo != None and photo or admin_content['photo']
          admin_content['video'] = video != None and video or admin_content['video']
          await other_function.send_content(message, user_idd, user_id, edit=True, send=False, admin_edit=True, admin_content=admin_content)


@dp.edited_message_handler(isUser(), content_types=types.ContentTypes.ANY, state="*")
async def edit_message_in_user(message: types.Message):
  chat, first_name, username, user_id = message.chat.id, message.from_user.first_name or '', message.from_user.username and f"@{message.from_user.username}" or "", str(
    message.from_user.id)

  photo, video = None, None
  if message.text != None:
    t = message.text
  else:
    try:
      t = message.caption or ''
      photo = message.photo[0].file_id
    except:
      t = message.caption
      try:
        video = message.video.file_id
      except:
        video = message.animation.file_id

  is_user_topic = await connect_bd.mongo_conn.db.topics.find_one({'user_id': user_id})
  if is_user_topic:
    if is_user_topic.get('history'):
      for message_id in is_user_topic['history']:
        hist = is_user_topic['history'][message_id]
        if hist.get('msg_user_id') == str(message.message_id):
          user_content = hist
          user_content['text'] = t
          user_content['photo'] = photo != None and photo or user_content['photo']
          user_content['video'] = video != None and video or user_content['video']
          is_user = await connect_bd.mongo_conn.db.users.find_one({'user_id': user_id})
          t, m = await keyboard.get_samples(dop_settings=True, visible_samples=False, settings=False, user=is_user,
            topic_id=is_user_topic['message_thread_id'])
          await other_function.send_content(message, topic_chat_id, user_id, user_topic=is_user_topic, edit=True, send=False, user_edit=True,
            user_content=user_content, message_thread_id=is_user_topic['message_thread_id'], message_id=message_id, reply_markup=m)

@dp.message_handler(isUser(), isPrivate(), isChat(chat_id=topic_chat_id), content_types=types.ContentTypes.ANY, state="*")
async def send_message_in_user(message: types.Message):
  chat, first_name, username, user_id = message.chat.id, message.from_user.first_name or '', message.from_user.username and f"@{message.from_user.username}" or "", str(message.from_user.id)

  if message.reply_to_message:
    if message.reply_to_message.forum_topic_created:
      user_idd = re.findall(r'[(]([0-9]+)', message.reply_to_message.forum_topic_created.name)[0]
      is_user_topic = await connect_bd.mongo_conn.db.topics.find_one({'user_id': user_idd})

      await other_function.send_content(message, user_idd, user_id, message_admin_id=message.message_id, user_topic=is_user_topic, admin_send=True)


@dp.message_handler(isUser(), content_types=types.ContentTypes.TEXT | types.ContentTypes.PHOTO | types.ContentTypes.VIDEO, state="*")
async def send_message_in_user(message: types.Message):
  chat, fullname, username, user_id = message.chat.id, message.from_user.full_name, message.from_user.username and f"@{message.from_user.username}" or "", str(message.from_user.id)
  try:
    if user_id not in conf['admin']['id']:
      is_user = await connect_bd.mongo_conn.db.users.find_one({'user_id': user_id})
      is_user_topic = await connect_bd.mongo_conn.db.topics.find_one({'user_id': user_id})

      if not is_user_topic:
        chat_u = await bot.get_chat(user_id)
        chat_info = await bot.create_forum_topic(topic_chat_id, name=f"{fullname} ({user_id})")
        t, m = await keyboard.get_samples(dop_settings=True, visible_samples=False, settings=False, user=is_user,
          topic_id=chat_info.message_thread_id)
        photo, contact = None, f'Контакт: <a href="tg://user?id={user_id}">{fullname}</a> {username}'
        if chat_u.photo:
          big_file_id = chat_u.photo.big_file_id
          file = await bot.download_file_by_id(big_file_id)
          m1 = await keyboard.get_admin_buttons(is_user)
          msg = await bot.send_photo(chat_id=topic_chat_id, photo=file,
            caption=contact,
            message_thread_id=chat_info.message_thread_id, reply_markup=m1)
          photo = msg.photo[len(msg.photo)-1].file_id
        else:
          m1 = await keyboard.get_admin_buttons(is_user)
          msg = await bot.send_message(chat_id=topic_chat_id, text=contact, message_thread_id=chat_info.message_thread_id, reply_markup=m1)

        is_user_topic = {'user_id': user_id, 'message_thread_id': chat_info.message_thread_id, 'name': chat_info.name, 'contact': contact, 'photo': photo, 'history': {}}
        await connect_bd.mongo_conn.db.topics.insert_one(is_user_topic)

        await other_function.send_content(message, topic_chat_id, user_id, message_thread_id=chat_info.message_thread_id, reply_markup=m, user_send=True, user_topic=is_user_topic)
        await bot.pin_chat_message(topic_chat_id, msg.message_id)
      else:
        t, m = await keyboard.get_samples(dop_settings=True, visible_samples=False, settings=False, user=is_user,
          topic_id=is_user_topic['message_thread_id'])
        await other_function.send_content(message, topic_chat_id, user_id, message_thread_id=is_user_topic['message_thread_id'], reply_markup=m, user_send=True, user_topic=is_user_topic)
  except Exception as e:
    print(e)
