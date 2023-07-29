import time


class OtherCommands():
  trash_data = {}
  bot, dp, types = None, None, None

  async def getTimeFormat(self, second):
    ts = time.gmtime(second)
    if second >= 86400:
      days = int(second / 86400)
    else:
      days = 0
    hour = time.strftime("%H", ts)
    min = time.strftime("%M", ts)
    sec = time.strftime("%S", ts)
    return f"{days}Д.{hour}Ч.{min}М.{sec}С."

  async def delete_commands(self, admin_id):
    await self.dp.bot.delete_my_commands(self.types.bot_command_scope.BotCommandScopeChat(admin_id))

  async def set_commands(self):
    await self.bot.set_my_commands([
    ], self.types.bot_command_scope.BotCommandScopeAllGroupChats())
    await self.bot.set_my_commands([
    ], self.types.bot_command_scope.BotCommandScopeAllPrivateChats('all_private_chats'))


  async def set_admin_commands(self, admins):
    for id in admins:
      try:
        await self.dp.bot.set_my_commands([
          self.types.BotCommand("mailing", "🔗 Рассылка"),
          self.types.BotCommand("restart", "🔄 Перезагрузка бота"),
          self.types.BotCommand("edit_welcome", "📝 Изменение приветствия"),
          self.types.BotCommand("edit_samples", "Шаблоны ответов")
        ], self.types.bot_command_scope.BotCommandScopeChat(id))
      except:
        pass

  async def set_trash(self, message=None, chat=None):
    if message != None:
      chat_id, message_id = 'message' not in message and [str(message.chat.id), message.message_id] or [
        str(message.message.chat.id), message.message.message_id]

      if self.trash_data.get(chat_id) == None:
        self.trash_data[chat_id] = []
      self.trash_data[chat_id].append(message_id)

    if chat:
      chat = str(chat)
      await self.delete_trash(chat)

  async def delete_trash(self, chat_id):
    if self.trash_data.get(chat_id):
      for message_id in self.trash_data[chat_id]:
        try:
          await self.bot.delete_message(chat_id, message_id)
        except Exception as e:
          pass

      del self.trash_data[chat_id]
