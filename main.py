import os
import sys
import json
import pprint
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

channel_secret = os.environ.get('channel_secret', None)
channel_access_token = os.environ.get('channel_access_token', None)
line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

bot = telepot.Bot(os.environ.get('telegram_token', None))
#//////////////////#
@app.route("/", methods=['GET'])
def index():
    return os.environ.get('index_show', '|ω・`)')

@app.route('/telegram', methods=['POST'])
def telegram():
    body = request.get_data(as_text=True)
    msg = json.loads(body)['message']
    content_type, chat_type, chat_id = telepot.glance(msg)
    chat_id = msg['chat']['id']
    message_id = msg['message_id']
    user_id = msg['from']['id']
    pprint.pprint(user_id)
    bot.sendMessage(chat_id,'ok')
    return 'OK'

@app.route("/line", methods=['POST'])
def line():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='got'))

    return 'OK'

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT', 5000)))
