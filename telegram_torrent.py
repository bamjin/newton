#!/usr/bin/python3.5

import sys
import os
import time
import feedparser
import telepot
import json
import requests
import atexit
import re
import random
import string
import urllib.request
from urllib import parse
from robobrowser import RoboBrowser
from apscheduler.schedulers.background import BackgroundScheduler
from telepot.delegate import per_chat_id, create_open, pave_event_space
from wakeonlan import wol

CONFIG_FILE = 'setting.json'

class DelugeAgent:
	def __init__(self, sender):
		self.STATUS_SEED = 'Seeding'
		self.STATUS_DOWN = 'Downloading'
		self.STATUS_ERR = 'Error'  # Need Verification
		self.weightList = {}
		self.sender = sender

	def downloadFromMagnet(self, magnet):
		os.system("deluge-console add " + magnet)

	def getCurrentList(self):
		return os.popen('deluge-console info').read()

	def printElement(self, e):
		outString = '이름: ' + e['title'] + '\n' + '상태: ' + e['status'] + '\n'
		outString += '진행율: ' + e['progress'] + '\n'
		outString += '\n'
		return outString

	def parseList(self, result):
		if not result:
			return
		outList = []
		for entry in result.split('\n \n'):
			title = entry[entry.index('Name:') + 6:entry.index('ID:') - 1]
			status = entry[entry.index('State:'):].split(' ')[1]
			ID = entry[entry.index('ID:') + 4:entry.index('State:') - 1]
			if status == self.STATUS_DOWN:
				progress = entry[entry.index('Progress:') + 10:entry.index('% [') + 1]
			else:
				progress = '0.00%'
			element = {'title': title, 'status': status, 'ID': ID, 'progress': progress}
			outList.append(element)
		return outList

	def isOld(self, ID, progress):
		if ID in self.weightList:
			if self.weightList[ID][0] == progress:
				self.weightList[ID][1] += 1
			else:
				self.weightList[ID][0] = progress
				self.weightList[ID][1] = 1
			if self.weightList[ID][1] > 3:
				return True
		else:
			self.weightList[ID] = [progress, 1]
			return False
		return False

	def check_torrents(self):
		currentList = self.getCurrentList()
		outList = self.parseList(currentList)
		if not bool(outList):
			self.sender.sendMessage('토렌트 리스트는 현재 비어 있습니다.')
			scheduler.remove_all_jobs()
			self.weightList.clear()
			return
		for e in outList:
			if e['status'] == self.STATUS_SEED:
				self.sender.sendMessage('다운로드 완료: {0}'.format(e['title']))
				self.removeFromList(e['ID'])
			elif e['status'] == self.STATUS_ERR:
				self.sender.sendMessage('다운로드 중지 (받을 수 없음): {0}\n'.format(e['title']))
				self.removeFromList(e['ID'])
			elif e['status'] == self.STATUS_DOWN:
				if self.isOld(e['ID'], e['progress']):
					self.sender.sendMessage('다운로드 중지 (진행안됨): {0}\n'.format(e['title']))
					self.removeFromList(e['ID'])
		return

	def removeFromList(self, ID):
		self.weightList.pop(ID)
		os.system("deluge-console del " + ID)

class Torrenter(telepot.helper.ChatHandler):
	YES = '<OK>'
	NO = '<NO>'
	MENU0 = '홈으로'
	MENU1 = '토렌트 검색해줘'
	MENU1_1 = '키워드 받기'
	MENU1_2 = '토렌트 선택'
	MENU2 = '지금 너 뭐 받고있어?'
	MENU10 = '중고나라 시세'
	MENU10_1 = '검색'
	rssUrl = """https://torrentkim3.net/bbs/rss.php?k="""
	GREETING = "무엇을 도와 드릴까요?."

	global scheduler
	SubtitlesLocation = ''  # Option: Input your subtitle location to save subtitle files,

	mode = ''
	navi = feedparser.FeedParserDict()

	def __init__(self, *args, **kwargs):
		super(Torrenter, self).__init__(*args, **kwargs)
		self.agent = self.createAgent(AGENT_TYPE)

	def createAgent(self, agentType):
		if agentType == 'deluge':
			return DelugeAgent(self.sender)

	def open(self, initial_msg, seed):
		self.menu()

	def menu(self):
		mode = ''
		show_keyboard = {'keyboard': [[self.MENU1, self.MENU2],  [self.MENU10], [self.MENU0]]}
		self.sender.sendMessage(self.GREETING, reply_markup=show_keyboard)

	def yes_or_no(self, comment):
		show_keyboard = {'keyboard': [[self.YES, self.NO], [self.MENU0]]}
		self.sender.sendMessage(comment, reply_markup=show_keyboard)

	def tor_get_keyword(self):
		self.mode = self.MENU1_1
		hide_keyboard = {'hide_keyboard': True}
		self.sender.sendMessage('검색 키워드를 입력해주세요.\n취소하시려면 "홈으로" 를 외쳐주세요.', reply_markup=hide_keyboard)

	def put_menu_button(self, l):
		menulist = [self.MENU0]
		l.append(menulist)
		return l

	def tor_search(self, keyword):
		self.mode = ''
		self.sender.sendMessage('토렌트 검색중입니다.. 1초만 기다려주세요.')
		self.navi = feedparser.parse(self.rssUrl + parse.quote(keyword))

		outList = []
		if not self.navi.entries:
			self.sender.sendMessage('검색결과가 없습니다ㅠㅠ. 다시 입력해주세요.')
			self.mode = self.MENU1_1
			return

		for (i, entry) in enumerate(self.navi.entries):
			if i == 15: break
			title = str(i + 1) + ". " + entry.title

			templist = []
			templist.append(title)
			outList.append(templist)

		show_keyboard = {'keyboard': self.put_menu_button(outList)}
		self.sender.sendMessage('어떤걸로 받을까요?', reply_markup=show_keyboard)
		self.mode = self.MENU1_2

	def tor_download(self, selected):

		self.mode = ''
		index = int(selected.split('.')[0]) - 1
		magnet = self.navi.entries[index].link
		self.agent.downloadFromMagnet(magnet)
		self.sender.sendMessage('다운로드를 시작합니다.')
		self.navi.clear()
		if not scheduler.get_jobs():
			scheduler.add_job(self.agent.check_torrents, 'interval', minutes=1)
		self.menu()

	def tor_show_list(self):
		self.mode = ''
		self.sender.sendMessage('토렌트 리스트를 확인중입니다..')
		result = self.agent.getCurrentList()
		if not result:
			self.sender.sendMessage('다운중인 토렌트가 없습니다.')
			return
		outList = self.agent.parseList(result)
		for e in outList:
			self.sender.sendMessage(self.agent.printElement(e))
		self.menu()

	def tor_get_search(self):
		self.mode = self.MENU10_1
		hide_keyboard = {'hide_keyboard': True}
		self.sender.sendMessage('뭘 사고 싶어요? \n취소하시려면 "홈으로" 를 외쳐주세요.', reply_markup=hide_keyboard)

	def joongo(self, search):
		self.mode = ''
		browser = RoboBrowser(history=True, parser='lxml')
		base_url = "https://nid.naver.com/nidlogin.login"
		browser.open(base_url)
		form = browser.get_form(action='https://nid.naver.com/nidlogin.login')

		form["id"] = 'NAVER ID'
		form["pw"] = 'NAVER PW'
		browser.session.headers['Referer'] = base_url
		browser.submit_form(form)

		joonggo_lists = []

		browser.open("http://m.cafe.naver.com/ArticleSearchList.nhn?search.query=" + \
        	urllib.request.quote(search) + \
			"&search.menuid=&search.searchBy=0&search.sortBy=sim&search.clubid=10050146")

		for li in browser.select('li'):
		    link = li.a.get('href')
		    title = li.a.h3
		    price = re.search(r'(\d+|,)+?\s?(만|만원|원)', str(li))
		    date = li.find('span', {'class': 'time'})

		    if "clubid" in link and title and price:
		        price = price.group(0)
		        if not price == "1원":
		            title = title.get_text()
		            link = "http://m.cafe.naver.com" + link
		            link = re.sub(r'&query=.+', '' , link)
		            date = date.get_text()
		            joonggo_lists.append(price + " " + title + " (" + date + ") " + link)

		self.sender.sendMessage("%s" % "\n".join(joonggo_lists))
		self.menu()

	def handle_command(self, command):

		if command == self.MENU0:
			self.menu()
		elif command == self.MENU1:
			self.tor_get_keyword()
		elif command == self.MENU2:
			self.tor_show_list()
		elif command == self.MENU10:     # Get Joongo Keyword
			self.tor_get_search()
		elif self.mode == self.MENU1_1:  # Get Torrent Keyword
			self.tor_search(command)
		elif self.mode == self.MENU1_2:  # Download Torrent
			self.tor_download(command)
		elif self.mode == self.MENU10_1: # Joongo Search
			self.joongo(command)

	def handle_smi(self, file_id, file_name):
		try:
			self.sender.sendMessage('자막 저장중..')
			bot.download_file(file_id, self.SubtitlesLocation + file_name)
		except Exception as inst:
			self.sender.sendMessage('오류: {0}'.format(inst))
			return
		self.sender.sendMessage('자막 파일을 저장했습니다.')

	def on_message(self, msg):
		content_type, chat_type, chat_id= telepot.glance(msg)

		# Check ID
		if not chat_id in VALID_USERS:
			self.sender.sendMessage("Who are you? Go away,bro.")
			return

		if content_type is 'text':
			self.handle_command(msg['text'])
			return

		if content_type is 'document':
			file_name = msg['document']['file_name']
			if file_name[-3:] == 'smi':
				file_id = msg['document']['file_id']
				self.handle_smi(file_id, file_name)
				return
			self.sender.sendMessage('인식할 수 없는 파일입니다.')
			return
		self.sender.sendMessage('인식하지 못했습니다')

	def on_close(self, exception):
		pass

def parseConfig(filename):
	f = open(filename, 'r')
	js = json.loads(f.read())
	f.close()
	return js

def getConfig(config):
	global TOKEN
	global AGENT_TYPE
	global VALID_USERS
	TOKEN = config['common']['token']
	AGENT_TYPE = config['common']['agent_type']
	VALID_USERS = config['common']['valid_users']



config = parseConfig(CONFIG_FILE)

if not bool(config):
	print("Err: Setting file is not found")
	exit()

getConfig(config)
scheduler = BackgroundScheduler()
scheduler.start()
bot = telepot.DelegatorBot(TOKEN, [
	pave_event_space()
	(per_chat_id(), create_open, Torrenter, timeout=120),
])
bot.message_loop(run_forever='Listening...')
