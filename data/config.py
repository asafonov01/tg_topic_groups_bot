from configobj import ConfigObj

conf = ConfigObj("data/settings.ini", encoding='UTF8')

bot_token = conf['aio']['bot_token']
topic_chat_id = conf['chat_with_topics']['id']