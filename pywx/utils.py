# coding: utf-8
from __future__ import unicode_literals

import ctypes
import random
import re
import time


RE_CHATROOM_USERNAME_PATTERN = re.compile(r'^@@\w+$')
RE_NORMAL_USERNAME_PATTERN = re.compile(r'^@\w+$')


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
