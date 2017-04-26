# coding: utf-8
from __future__ import unicode_literals

import re
import os.path
from logging import config

import enum


APP_ID = 'wx782c26e4c19acffb'


# HTTP
DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/57.0.2987.110 Safari/537.36'
)
DEFAULT_HEADERS = {
    'User-Agent': DEFAULT_USER_AGENT
}
DEFAULT_TIMEOUT = 1


# Wechat API
WX_BASE_URL = 'https://wx.qq.com'
WX_LOGIN_URL = 'https://login.wx.qq.com'
WX_WEBPUSH_URL = 'https://webpush.wx.qq.com'
WX_CGI_PATH = 'cgi-bin/mmwebwx-bin'
WX_QRIMG_BASE_URL = os.path.join(WX_LOGIN_URL, 'qrcode')
WX_JSLOING_URL = os.path.join(WX_LOGIN_URL, 'jslogin')
WX_LOING_CHECK_URL = os.path.join(WX_LOGIN_URL, WX_CGI_PATH, 'login')
WX_LOGOUT_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxlogout')
WX_INIT_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxinit')
WX_STATUS_NOTIFY_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxstatusnotify')
WX_SYNC_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxsync')
WX_GET_CONTACT_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxgetcontact')
WX_BATCH_GET_CONTACTS_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxbatchgetcontact')
WX_SYNC_CHECK_URL = os.path.join(WX_WEBPUSH_URL, WX_CGI_PATH, 'synccheck')
WX_SEND_TEXT_MESSAGE_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxsendmsg')
WX_SEND_IMG_MESSAGE_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxsendmsgimg')
WX_SEND_EMOTION_MESSAGE_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxsendemoticon')
WX_SEND_APPMSG_MESSAGE_URL = os.path.join(WX_BASE_URL, WX_CGI_PATH, 'webwxsendappmsg')


# Regex
RE_JSLOGING_PATTERN = re.compile(
    r'window.QRLogin.code = (?P<retcode>\d{3}); window.QRLogin.uuid = "(?P<uuid>\S+)";'
)
RE_LOGING_CHECK_PATTERN = re.compile(r'window.code=200;\nwindow.redirect_uri="(?P<redirect_url>.+?)"')
RE_SYNC_CHECK_PATTERN = re.compile(r'window.synccheck={retcode:"(?P<retcode>\d+)",selector:"(?P<selector>\d+)"}')


class StatusNotifyCode(enum.IntEnum):
    ENTER_SESSION = 2
    INITED = 3
    SYNC_CONV = 4
    QUIT_SESSION = 5


MESSAGE_TYPE = {
    51: 'system'
}


# Logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s %(asctime)s %(module)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        },
    }
}

config.dictConfig(LOGGING_CONFIG)
