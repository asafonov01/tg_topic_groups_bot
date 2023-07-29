from loader import dp, types, bot, connect_bd, topic_chat_id, conf, isChat, keyboard, FSMContext
from filters.filter_commands import isPrivate, isMessageButtons
from utils.functions import Func

other_function = Func()

@dp.callback_query_handler(isPrivate(), isMessageButtons(), state="*")
async def callback_data(message: types.CallbackQuery, state: FSMContext):
  chat, message_id, user_id = str(message.message.chat.id), message.message.message_id, str(message.from_user.id)
  d = message.data.split(":")
  is_user = await connect_bd.mongo_conn.db.users.find_one({'user_id': d[1]})
  is_user_topic = await connect_bd.mongo_conn.db.topics.find_one({'user_id': d[1]})

  if d[0] == 'block_user':
    if is_user:
      if is_user.get('is_banned') != None:
        if is_user.get('is_banned') == False:
          await connect_bd.mongo_conn.db.users.update_one({'user_id': d[1]}, {'$set': {'is_banned': True}})
          is_user['is_banned'] = True
        else:
          await connect_bd.mongo_conn.db.users.update_one({'user_id': d[1]}, {'$set': {'is_banned': False}})
          is_user['is_banned'] = False
      else:
        await connect_bd.mongo_conn.db.users.update_one({'user_id': d[1]}, {'$set': {'is_banned': False}})
        is_user['is_banned'] = False

      m = await keyboard.get_admin_buttons(is_user)
      if is_user_topic.get('photo'):
        await bot.edit_message_media(types.InputMediaPhoto(media=is_user_topic['photo'], caption=is_user_topic['contact']), topic_chat_id,
          inline_message_id=is_user_topic['message_thread_id'], message_id=message_id, reply_markup=m)
      else:
        await bot.edit_message_text(is_user_topic['contact'], topic_chat_id, inline_message_id=is_user_topic['message_thread_id'], message_id=message_id, reply_markup=m)


  if d[0] == 'samples_variant':
    t, m = await keyboard.get_samples(dop_settings=False, visible_samples=True, settings=False, user=is_user, sample=True)
    await other_function.send_content(message, topic_chat_id, user_id, message_thread_id=is_user_topic['message_thread_id'],
      reply_markup=m, user_send=True, user_topic=is_user_topic, send=False, edit=True, message_id=message_id, samples_variant=True)

  if d[0] == 'exit_select_samples':
    t, m = await keyboard.get_samples(dop_settings=True, visible_samples=False, settings=False, user=is_user)
    await other_function.send_content(message, topic_chat_id, user_id, message_thread_id=is_user_topic['message_thread_id'],
      reply_markup=m, user_send=True, user_topic=is_user_topic, send=False, edit=True, message_id=message_id, samples_variant=True)

  if d[0] == 'select_send':
    sample = await connect_bd.mongo_conn.db.samples.find_one({'id': d[2]})
    m = await keyboard.get_button_for_sample(sample)
    await bot.send_message(is_user['user_id'], sample['text'], reply_markup=m)
    if is_user_topic['history'][str(message_id)].get('samples') == None:
      is_user_topic['history'][str(message_id)]['samples'] = []
    is_user_topic['history'][str(message_id)]['samples'].append(sample['id'])

    await connect_bd.mongo_conn.db.topics.update_one({'user_id': is_user['user_id']}, {'$set': {'history': is_user_topic['history']}})

    t, m = await keyboard.get_samples(dop_settings=True, visible_samples=False, settings=False, user=is_user)
    await other_function.send_content(message, topic_chat_id, user_id, message_thread_id=is_user_topic['message_thread_id'],
      reply_markup=m, user_send=True, user_topic=is_user_topic, send=False, edit=True, message_id=message_id, sample_send=True)