# coding: utf-8
from __future__ import unicode_literals

import ctypes
import random
import re
import time


RE_CHATROOM_USERNAME_PATTERN = re.compile(r'^@@\w+$')
RE_NORMAL_USERNAME_PATTERN = re.compile(r'^@\w+$')

RE_SPAN_PATTERN = re.compile(r'<span class=".*?"></span>')
RE_EMOJI_PATTERN = re.compile(r'emoji(?P<emoji_code>[0-9a-z]+)')


def chunks(iterable, chunk_size):
    iterable = list(iterable)
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i: i + chunk_size]


def timestamp_now():
    return int(time.time() * 1000)


def bitwise_not(n):
    return -ctypes.c_int(n ^ 0).value - 1


def gen_device_id():
    return 'e%s' % int(random.random() * 1e15)


def gen_client_msg_id():
    return '%d%04d' % (int(time.time() * 1000), int(random.random() * 1e4))


def is_chatroom(member):
    return member['Sex'] == 0 and RE_CHATROOM_USERNAME_PATTERN.match(member['UserName'])


def is_mp(member):
    return member['Sex'] == 0 and RE_NORMAL_USERNAME_PATTERN.match(member['UserName'])


def is_friend(member):
    return member['Sex'] != 0 and RE_NORMAL_USERNAME_PATTERN.match(member['UserName'])


def emoji_formatter(content):

    def decode_emoji(match):
        emoji_code = RE_EMOJI_PATTERN.search(match.group()).group('emoji_code')
        emoji_stirng = b'\U000%s' % emoji_code
        return ' %s ' % emoji_stirng.decode('unicode-escape')

    return RE_SPAN_PATTERN.sub(decode_emoji, content)
