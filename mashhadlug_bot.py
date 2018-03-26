import telepot
from pprint import pprint
from telepot.loop import MessageLoop
from pytz import timezone
from datetime import datetime
from time import time

BOT_TOKEN_KEY = 'TOKEN'
BURST_THRESHOLD_SECS = 5
USER_MAXIMUM_BURST_POSTS = 3
READONLY_TIME_HOUR = 7

bot = telepot.Bot(BOT_TOKEN_KEY)
tz = timezone('Asia/Tehran')
hot_words = ('foo', 'bar')
users = {}

def handle(msg):
  content_type, chat_type, chat_id = telepot.glance(msg)
  msg_id = telepot.message_identifier(msg)
  if chat_type != 'group':
    return

  # Group is read-only before 7 oclock
  now = datetime.now(tz)
  if now.hour <= READONLY_TIME_HOUR:
    bot.deleteMessage(telepot.message_identifier(msg))
    return

  # Any GIF sent to the group should be removed
  if content_type == 'document' and msg['document']['mime_type'] == 'video/mp4':
    bot.deleteMessage(telepot.message_identifier(msg))
    return

  # Any post contaning hot words should also be removed
  if content_type == 'text':
    for word in hot_words:
      if word.lower() in msg['text'].lower():
        bot.deleteMessage(telepot.message_identifier(msg))
        return

  # Delete all messages sent from a user in a short period of time
  user_id = msg['from']['id']
  now = time()
  if users.get(user_id):
    users[user_id]['counts'] += 1
    if (now - users[user_id]['datetime']) < BURST_THRESHOLD_SECS:
      users[user_id]['datetime'] = now
      users[user_id]['ids'].append(msg_id)
      if users[user_id]['counts'] > USER_MAXIMUM_BURST_POSTS:
        for msg_id in users[user_id]['ids']:
          bot.deleteMessage(msg_id)
        users[user_id]['ids'] = []
    else:
      users[user_id] = {'counts': 1, 'datetime': now, 'ids': [msg_id]}
  else:
    users[user_id] = {'counts': 1, 'datetime': now, 'ids': [msg_id]}


MessageLoop(bot, handle).run_as_thread()
