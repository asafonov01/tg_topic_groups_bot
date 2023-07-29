
async def start(dp):
  import filters
  from loader import other_commands, types, bot, conf, connect_bd

  bot_info = await bot.get_me()
  bot['username'] = bot_info.username
  print(bot_info)

  other_commands.bot = bot
  other_commands.dp = dp
  other_commands.types = types

  filters.setup(dp)
  await connect_bd.mongo_conn.connect_server()

  if conf['admin']['id']:
    await other_commands.set_admin_commands(conf['admin']['id'])

if __name__ == '__main__':
  from aiogram import executor
  from handlers import dp

  executor.start_polling(dp, on_startup=start, skip_updates=True)