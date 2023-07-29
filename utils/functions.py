import asyncio

from loader import connect_bd, bot, types, exceptions, topic_chat_id, keyboard

class Func:
  async def send_content(self, message, chat_id, user_id, send=True, edit=False, message_id='', message_admin_id='',
    message_thread_id=None, reply_markup=None, user_send=False, user_topic=None, admin_edit=False, admin_content=None, user_content=None, admin_send=False, user_edit=False, samples_variant=False, sample_send=False):
    photo, video, sample_sended = None, None, ''

    if user_topic:
      if user_topic.get('history'):
        if user_topic['history'].get(str(message_id)) == None:
          user_topic['history'][str(message_id)] = {}

        if user_topic['history'][str(message_id)].get('samples'):
          sample_ids, sample_sended, i = {}, f'\n\nОтправлены шаблоны:', 1
          async for sample in connect_bd.mongo_conn.db.samples.find():
            if sample['id'] in user_topic['history'][str(message_id)]['samples']:
              sample_ids[sample['id']] = sample['text']

          for id in user_topic['history'][str(message_id)]['samples']:
            sample_sended += f"\n<b>{i}. {sample_ids[id]}</b>"
            i += 1

    if send:
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

      thread_id = message_thread_id
      while True:
        try:
          if photo:
            msg = await bot.send_photo(chat_id, photo=photo, message_thread_id=thread_id, caption=t,
              reply_markup=reply_markup)
          elif video:
            msg = await bot.send_video(chat_id, video=video, message_thread_id=thread_id, caption=t,
              reply_markup=reply_markup)
          else:
            msg = await bot.send_message(chat_id, t, message_thread_id=thread_id, reply_markup=reply_markup)
          break
        except Exception as e:
          if str(e) == 'Message thread not found':
            try:
              is_user = await connect_bd.mongo_conn.db.users.find_one({'user_id': user_id})
              chat_u = await bot.get_chat(user_id)
              chat_info = await bot.create_forum_topic(topic_chat_id, name=f"{is_user['fullname']} ({user_id})")
              photo1, contact = None, f'Контакт: <a href="tg://user?id={user_id}">{is_user["fullname"]}</a> {is_user["username"]}'
              m1 = await keyboard.get_admin_buttons(is_user)
              if chat_u.photo:
                big_file_id = chat_u.photo.big_file_id
                file = await bot.download_file_by_id(big_file_id)
                ms = await bot.send_photo(chat_id=topic_chat_id, photo=file,
                  caption=f'Контакт: <a href="tg://user?id={user_id}">{is_user["fullname"]}</a> {is_user["username"]}',
                  message_thread_id=chat_info.message_thread_id, reply_markup=m1)
                photo1 = ms.photo[len(ms.photo) - 1].file_id
              else:
                ms = await bot.send_message(chat_id=topic_chat_id,
                  text=f'Контакт: <a href="tg://user?id={user_id}">{is_user["fullname"]}</a> {is_user["username"]}',
                  message_thread_id=chat_info.message_thread_id, reply_markup=m1)
              thread_id = chat_info.message_thread_id
              user_topic['message_thread_id'] = thread_id
              is_user_topic = {'user_id': user_id, 'message_thread_id': thread_id, 'name': chat_info.name, 'contact': contact, 'photo': photo1, 'history': {}}
              await connect_bd.mongo_conn.db.topics.insert_one(is_user_topic)
              await connect_bd.mongo_conn.db.topics.delete_one({'user_id': user_id})
              await bot.pin_chat_message(topic_chat_id, ms.message_id)
            except Exception as e:
              pass


    if edit:
      if not admin_edit:
        if not user_edit:
          edit_content = user_topic['history'][str(message_id)]
        else:
          edit_content = user_content
      else:
        edit_content = admin_content

      if edit_content['photo']:
        if not admin_edit:
          msg = await bot.edit_message_media(
            types.InputMediaPhoto(media=edit_content['photo'], caption=edit_content['text']+sample_sended), chat_id, inline_message_id=message_thread_id,message_id=message_id, reply_markup=reply_markup)
        else:
          msg = await bot.edit_message_media(
            types.InputMediaPhoto(media=edit_content['photo'], caption=edit_content['text']), edit_content['user_id'], message_id=edit_content['message_user_id'])
      elif edit_content['video']:
        if not admin_edit:
          msg = await bot.edit_message_media(
            types.InputMediaVideo(media=edit_content['video'], caption=edit_content['text']+sample_sended), chat_id,
            inline_message_id=message_thread_id, message_id=message_id, reply_markup=reply_markup)
        else:
          msg = await bot.edit_message_media(
            types.InputMediaVideo(media=edit_content['video'], caption=edit_content['text']), edit_content['user_id'],
            message_id=edit_content['message_user_id'])
      else:
        if not admin_edit:
          msg = await bot.edit_message_text(edit_content['text']+sample_sended, chat_id, inline_message_id=message_thread_id, message_id=message_id,
            reply_markup=reply_markup)
        else:
          msg = await bot.edit_message_text(edit_content['text'], edit_content['user_id'], message_id=edit_content['message_user_id'])

      if not admin_edit and not user_edit:
        edit_content = user_topic['history'][str(message_id)]
        t = edit_content['text']

    if not admin_edit and not user_edit and not samples_variant and not sample_send:
      if user_send:
        obj = {}
        if user_topic.get('history') == None:
          obj['history'] = {}
          obj['history'][str(msg.message_id)] = {'text': t, 'photo': photo, 'video': video, 'msg_user_id': str(message.message_id)}
        else:
          obj = user_topic
          del obj['_id']
          obj['history'][str(msg.message_id)] = {'text': t, 'photo': photo, 'video': video, 'msg_user_id': str(message.message_id)}

        await connect_bd.mongo_conn.db.topics.update_one({'user_id': user_id}, {'$set': obj})

      if admin_send:
        obj = {}
        if user_topic.get('admin_history') == None:
          obj['admin_history'] = {}
          obj['admin_history'][str(message_admin_id)] = {'text': t, 'photo': photo, 'video': video, 'message_user_id': str(msg.message_id)}
        else:
          obj = user_topic
          del obj['_id']
          obj['admin_history'][str(message_admin_id)] = {'text': t, 'photo': photo, 'video': video, 'message_user_id': str(msg.message_id)}
        await connect_bd.mongo_conn.db.topics.update_one({'user_id': user_topic['user_id']}, {'$set': obj})

    return msg

