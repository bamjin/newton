# Newton

This is Telegram BOT which can search the torrent seed and download to where you want.
Also, it can search the price of second-hand items which you want to buy.
But, it search only Korean torrent seed site (torrentkim) and Second-hand site (joonggo-nara).
It is a reason why **it works ONLY in KOREA.**

## Installation

- **Install python packages**
```bash
$ pip install telepot
```
 and, it will be needed to add your bot token in *settings.json* file
 You should create your bot with @Botfather in telgram.
 Then, you can get your token using  */token*  message.
 *For more details: http://telepot.readthedocs.io/en/latest/*

```bash
$ pip install feedparser
```
**Here is very important part to fix an error.**
This application is written by python 3 or higher.
But, there is no **sgmllib.py** which feedparser need to work.
So, we need to copy from python 2 library folder, then paste to python 3 library folder.
*For more details: https://pypi.python.org/pypi/feedparser*

In my case, I could find **sgmllib.py** in **/usr/lib/python2.7**
If you are using normal python 3, you need to copy and paste in **/usr/lib/python3.#**
Or, if you use pyenv to control your python versions, you should paste in
**/home/USERNAME/.pyenv/versions/#.#.#(PythonVersionNo)/lib/python3.#**
Then, you should run 2to3 in that file path
```bash
$ 2to3 -w sgmllib.py		# To change python version
```
Finally, you need to remove the ***warnpy3k*** 4 lines at the top of the file.

```bash
$ pip install Robobrowser apscheduler		# To login Naver
```

- **Install torrent client**
```bash
$ sudo apt-get install deluge-common deluged deluge-console
```

- **Start deluge**
```bash
$ deluged
$ vi ~/.config/deluge/auth
.
.
User:Password:10			# Add to auth ex)bamjin:qwer!@#$:10
```

If you wanted to use deluge with web browser, you can just install deluge-web.
```bash
$ sudo apt-get install deluge-web		#install deluge-web
$ deluge-web --fork					#start deluge-web in background
```

 - **Edit setting.json**
```json
{
  "common": {
    "token": "1234567:blahblahYour Bot token",
    "valid_users": [
      12345678
    ],
    "agent_type": "deluge"
  }
}
```
**token** is your bot token which you got when you make a new bot using *@Botfather*

**vaild_users** should be filled in 8 digit number which every telegram user have.
If you want to make your bot as public bot, you don't need to fill in vaild_users.
You can check your 8 digit number through telegram bot named *@my_bot_id*

## Run
```bash
$ python3 telegram_torrent.py

or

$ python telegram_torrent.py 		# if you use pyenv
```
