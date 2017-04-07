import os
import sys
import json
import pprint
import telepot
import requests
import psycopg2
import urllib.parse as urlparse
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ConfirmTemplate, PostbackTemplateAction, MessageTemplateAction

app = Flask(__name__)
channel_secret = os.environ.get('channel_secret', None)
channel_access_token = os.environ.get('channel_access_token', None)
line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)
bot = telepot.Bot(os.environ.get('telegram_token', None))
urlparse.uses_netloc.append('postgres')
url = urlparse.urlparse(os.environ['DATABASE_URL'])
bot = telepot.Bot(os.environ.get('telegram_token', None))
def kobe(**args):
	conn = psycopg2.connect(database=url.path[1:],user=url.username,password=url.password,host=url.hostname,port=url.port)
	cur = conn.cursor()
	if args['status'] == 'new':
		cur.execute("insert into %s (uid,client,content) values ('%s','%s','%s','%s');" % (args['table'],args['uid'],args['client'],args['content']))
		conn.commit()
	elif args['status'] == 'read':
		cur.execute("select * from %s where uid = '%s' and client = '%s';" % (args['table'],args['uid'],args['client']))
		global query
		query = cur.fetchall()
	elif args['status'] == 'all':
		cur.execute("select * from data;")
		query = cur.fetchall()
	elif args['status'] == 'update':
		kobe(status='read',table=args['table'],uid=args['uid'],client=args['client'])
		if query == []:
			kobe(status='new',table=args['table'],uid=args['uid'],client=args['client'],content=args['content'])
		else:
			conn = psycopg2.connect(database=url.path[1:],user=url.username,password=url.password,host=url.hostname,port=url.port)
			cur = conn.cursor()
			cur.execute("update %s set content = '%s' where uid = '%s' and client = '%s';" % (args['table'],args['content'],args['uid'],args['client']))
			conn.commit()
	elif args['status'] == 'del':
		cur.execute("delete from data where uid = '%s' and client = '%s';" % (args['uid'],args['client']))
		conn.commit()
	elif args['status'] == 'kobe':
		kobe(status='read',table='data',uid=args['uid'],client=args['client'])
		uid = query[0][0]
		client = query[0][1]
		content = query[0][2]
		kobe(status='new',table='kobe',uid=uid,client=client,content=content)
		kobe(status='del',uid=uid,client=client)

@app.route("/", methods=['GET'])
def index():
	return os.environ.get('index_show', '|ω・`)')

@app.route("/fbpost", methods=['POST'])
def fbpost():
	def kobe_post():
		conn = psycopg2.connect(database=url.path[1:],user=url.username,password=url.password,host=url.hostname,port=url.port)
		cur = conn.cursor()
		try:
			cur.execute("select * from kobe;")
			global query
			query = cur.fetchall()[0][3]
		except IndexError:
			return
		cur.execute("select * from post_count;")
		global count
		count = cur.fetchall()[0][0]
		cur.execute("update post_count set status = status + 1;")
		conn.commit()
		cur.execute("delete from kobe where (uid,client,content) in (select uid,client,content from kobe limit 1);")
		conn.commit()
		return '#靠北嘉藥%d\n%s' % (int(count),query)
	def post(text):
		url = 'https://graph.facebook.com/v2.8/1432123710172673/feed/'
		try:
			payload = {'message': text,'access_token': os.environ.get('facebook_token', None)}
		except TypeError:
			return
		if text is None:
			return
		r = requests.post(url, data=payload)
		loads = json.loads(r.text)
		pprint.pprint(loads)
		if 'error' in loads:
			bot.sendMessage(int(os.environ.get('telegram_token', None)),'Post Error.')
	body = request.get_data(as_text=True)
	try:
		fbpost_js = json.loads(body)
	except:
		return 'OK'
	if fbpost_js['token'] == os.environ['custom_token']:
		post(kobe_post())
	return 'OK'

@app.route('/telegram', methods=['POST'])
def telegram():
	body = request.get_data(as_text=True)
	msg = json.loads(body)['message']
	content_type, chat_type, chat_id = telepot.glance(msg)
	chat_id = msg['chat']['id']
	message_id = msg['message_id']
	user_id = msg['from']['id']
	hide_keyboard = {'hide_keyboard': True}
	client = 'telegram'
	if content_type == 'text':
		command = msg['text'].lower()
		say = msg['text']
		if command == '/start':
			bot.sendMessage(chat_id,'今天有什麼事要靠北嗎？',reply_markup=hide_keyboard)
		elif command == '對啊':
			kobe(status='read',table='data',uid=user_id,client=client)
			try:
				if query[0][3] == '':
					bot.sendMessage(chat_id,'不然你是要靠北什麼030...',reply_markup=hide_keyboard)
					return 'OK'
			except IndexError:
				bot.sendMessage(chat_id,'呃 好像出錯了？\nerr #IndexError')
				return 'OK'
			bot.sendMessage(chat_id,'✈️感謝你的使用,通常等候時間十分鐘',reply_markup=hide_keyboard)
			kobe(status='kobe',table='kobe',uid=user_id,client=client)
		elif command == '算了':
			kobe(status='read',table='data',uid=user_id,client=client)
			try:
				print(query)
				if query[0][3] == '':
					bot.sendMessage(chat_id,'不要裝好人(´･_･`)',reply_markup=hide_keyboard)
					return 'OK'
			except IndexError:
				bot.sendMessage(chat_id,'呃 好像出錯了？\nerr #IndexError',reply_markup=hide_keyboard)
				return 'OK'
			bot.sendMessage(chat_id,'大大真寬宏大量～',reply_markup=hide_keyboard)
			kobe(status='update',table='data',uid=user_id,client=client,content='')
		else:
			markup = ReplyKeyboardMarkup(keyboard=[['對啊','算了']])
			bot.sendMessage(chat_id,'靠北完了嗎？',reply_markup=markup,reply_to_message_id=message_id)
			kobe(status='update',table='data',uid=user_id,client=client,content=say)
	return 'OK'

@app.route("/line", methods=['POST'])
def callback():
	def ltext(reply):
		return TextSendMessage(text=reply)
	signature = request.headers['X-Line-Signature']
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)
	try:
		events = parser.parse(body, signature)
	except InvalidSignatureError:
		abort(400)
	client = 'line'
	msg = json.loads(body)['events'][0]
	user_id = msg['source']['userId']
	try:
		content_type = msg['message']['type']
		reply_to = msg['replyToken']
		say = msg['message']['text']
		command = say.lower()
	except:
		content_type = msg['type']
	if content_type == 'text':
		if command == '對啊' or command == '1':
			kobe(status='read',table='data',uid=user_id,client=client)
			try:
				if query[0][3] == '':
					line_bot_api.reply_message(reply_to,ltext('不然你是要靠北什麼030...'))
					return 'OK'
			except IndexError:
				line_bot_api.reply_message(reply_to,ltext('不然你是要靠北什麼030...'))
				return 'OK'
			line_bot_api.reply_message(reply_to,ltext('✈️感謝你的使用,通常等候時間十分鐘'))
			kobe(status='kobe',table='kobe',uid=user_id,client=client)
		elif command == '算了' or command == '2':
			kobe(status='read',table='data',uid=user_id,client=client)
			try:
				if query[0][3] == '':
					line_bot_api.reply_message(reply_to,ltext('不要裝好人(´･_･`)'))
					return 'OK'
			except IndexError:
				line_bot_api.reply_message(reply_to,ltext('不然你是要靠北什麼030...'))
				return 'OK'
			line_bot_api.reply_message(reply_to,ltext('大大真寬宏大量～'))
			kobe(status='update',table='data',uid=user_id,client=client,content='')
		else:
			line_bot_api.reply_message(reply_to,TemplateSendMessage(alt_text='靠北完了嗎？\n電腦版請手動打選項\n1 = 對啊,2 = 算了',template=ConfirmTemplate(text='靠北完了？\n%s' % (say),actions=[PostbackTemplateAction(label='對啊',text='對啊',data='post'),MessageTemplateAction(label='算了',text='算了')])))
			kobe(status='update',table='data',uid=user_id,client=client,content=say)
	return 'OK'

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=int(os.environ.get('PORT', 5000)))
