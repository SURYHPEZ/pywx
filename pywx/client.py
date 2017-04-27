# coding: utf-8
from __future__ import unicode_literals

import logging
import os.path
import threading
from itertools import chain

import gevent
import gevent.monkey
import requests
from lxml import etree
from six import StringIO
from PIL import Image

from pywx import config
from pywx.models import (
    User, Contact, ContactSet, Message
)
from pywx.utils import (
    chunks, gen_device_id, timestamp_now, bitwise_not,
    gen_client_msg_id
)


logger = logging.getLogger(__name__)


class WXClient(object):

    MESSAGE_HANDLERS = {
        item.value: item.name.lower()
        for item in config.MessageType
    }

    def __init__(self):
        self._online = False
        self.session = requests.Session()
        self.session.headers.update(config.DEFAULT_HEADERS)

        self.device_id = gen_device_id()
        self.uin = None
        self.pass_ticket = None
        self.sid = None
        self.skey = None
        self.user = None
        self.sync_key = None

        self.contacts = ContactSet()

    @property
    def lang(self):
        return self.session.cookies.get('mm_lang', 'zh_CN')

    @property
    def sync_key_str(self):
        if not self.sync_key:
            return
        return '|'.join((
            '%s_%s' % (kv['Key'], kv['Val'])
            for kv in self.sync_key['List']
        ))

    @property
    def online(self):
        return self._online

    def login(self):
        self._login()
        self._initialize()
        self._start_sync()

    def logout(self):
        params = {
            'redirect': 1,
            'type': 1,
            'skey': self.skey
        }
        data = {
            'sid': self.sid,
            'uin': self.uin
        }
        self.session.post(config.WX_LOGOUT_URL, params=params, data=data)
        self._online = False

    def _login(self):
        uuid = self._get_login_uuid()
        if not uuid:
            return
        qrimg = self._get_qrimg(uuid)
        qrimg.show()
        while not self._online:
            success, login_info_url = self._login_check(uuid)
            if not success:
                continue
            login_info = self._get_login_info(login_info_url)
            self._process_login_info(login_info)
            self._online = True

    def _get_login_uuid(self):
        params = {
            'appid': config.APP_ID,
            'fun': 'new',
        }
        res = self.session.get(config.WX_JSLOING_URL, params=params, timeout=config.DEFAULT_TIMEOUT)
        match = config.RE_JSLOGING_PATTERN.search(res.content)
        if not match:
            return
        return match.group('uuid')

    def _get_qrimg(self, uuid):
        qrimg_url = os.path.join(config.WX_QRIMG_BASE_URL, uuid)
        res = self.session.get(qrimg_url, timeout=config.DEFAULT_TIMEOUT)
        qrimg = Image.open(StringIO(res.content))
        return qrimg

    def _login_check(self, uuid):
        local_time = timestamp_now()
        params = {
            'loginicon': 'true',
            'uuid': uuid,
            'tip': 0,
            'r': bitwise_not(local_time),
            '_': local_time
        }
        res = self.session.get(config.WX_LOING_CHECK_URL, params=params)
        match = config.RE_LOGING_CHECK_PATTERN.search(res.content)
        if not match:
            return False, None
        return True, match.group('redirect_url')

    def _get_login_info(self, login_info_url):
        res = self.session.get(login_info_url, allow_redirects=False, timeout=config.DEFAULT_TIMEOUT)
        document = etree.fromstring(res.content)
        return {elem.tag: elem.text for elem in document}

    def _process_login_info(self, login_info):
        self.uin = login_info['wxuin']
        self.pass_ticket = login_info['pass_ticket']
        self.skey = login_info['skey']
        self.sid = login_info['wxsid']

    def _notify_mobile(self, status_code, to_username=None):
        params = {
            'pass_ticket': self.pass_ticket
        }
        data = self._gen_base_request()
        data.update({
            'ClientMsgId': timestamp_now(),
            'Code': status_code,
            'FromUserName': self.user.username,
            'ToUserName': to_username or self.user.username
        })
        self.session.post(
            config.WX_STATUS_NOTIFY_URL, params=params, json=data, timeout=config.DEFAULT_TIMEOUT
        )

    def _initialize(self):
        params = {
            'r': bitwise_not(timestamp_now()),
            'pass_ticket': self.pass_ticket,
        }
        data = self._gen_base_request()
        res = self.session.post(config.WX_INIT_URL, params=params, json=data)
        res.encoding = 'UTF-8'
        init_data = res.json()
        user = init_data['User']
        self.user = User(
            uin=user['Uin'], username=user['UserName'], nickname=user['NickName'], raw=user
        )
        self.sync_key = init_data['SyncKey']
        for contact in init_data['ContactList']:
            contact = Contact.from_wx_contact(self, contact)
            self.contacts.add_or_update(contact)

        self._notify_mobile(config.StatusNotifyCode.INITED.value)
        self._init_contacts()
        chatroom_usernames = (chatroom.username for chatroom in self.contacts.chatroooms)
        self._batch_get_contacts(chatroom_usernames)

    def _init_contacts(self):
        params = {
            'pass_ticket': self.pass_ticket,
            'r': timestamp_now(),
            'seq': 0,
            'skey': self.skey,
            'lang': self.lang,
        }
        res = self.session.get(config.WX_GET_CONTACT_URL, params=params)
        res.encoding = 'UTF-8'
        res_data = res.json()
        for member in res_data['MemberList']:
            contact = Contact.from_wx_contact(self, member)
            self.contacts.add_or_update(contact)

    def _batch_get_contacts(self, usernames, encry_chatroom_id=None):

        def _get_contacts(usernames):
            params = {
                'type': 'ex',
                'r': timestamp_now(),
                'pass_ticket': self.pass_ticket
            }
            data = self._gen_base_request()
            data.update({
                'Count': len(usernames),
                'List': [
                    {
                        'EncryChatRoomId': encry_chatroom_id or '',
                        'UserName': username
                    }
                    for username in usernames
                ]
            })
            res = self.session.post(config.WX_BATCH_GET_CONTACTS_URL, params=params, json=data)
            res.encoding = 'UTF-8'
            res_data = res.json()
            return res_data['ContactList']

        jobs = [gevent.spawn(_get_contacts, chunk) for chunk in chunks(usernames, 50)]
        gevent.joinall(jobs)
        contacts_iter = chain(*(job.value for job in jobs))

        return contacts_iter

    def _start_sync(self):

        def _sync():
            while self.online:
                selector = self._sync_check()
                if selector == 0:
                    continue
                self._sync_message()

        sync_thread = threading.Thread(target=_sync)
        sync_thread.setDaemon(True)
        sync_thread.start()

    def _sync_check(self):
        params = {
            'r': timestamp_now(),
            'skey': self.skey,
            'sid': self.sid,
            'uin': self.uin,
            'deviceid': self.device_id,
            'synckey': self.sync_key_str,
            '_': timestamp_now(),
        }
        res = self.session.get(config.WX_SYNC_CHECK_URL, params=params)
        match = config.RE_SYNC_CHECK_PATTERN.search(res.content)
        if not match:
            return
        selector = int(match.group('selector'))
        return selector

    def _sync_message(self):
        params = {
            'sid': self.sid,
            'skey': self.skey,
            'pass_ticket': self.pass_ticket
        }
        data = self._gen_base_request()
        data.update({
            'SyncKey': self.sync_key,
            'rr': bitwise_not(timestamp_now())
        })
        res = self.session.post(config.WX_SYNC_URL, params=params, json=data)
        res.encoding = 'UTF-8'
        res_data = res.json()

        self.sync_key = res_data['SyncKey']
        message_list = res_data['AddMsgList']
        self._process_messages(message_list)

    def _process_messages(self, messages):
        for message in messages:
            message_type = self.MESSAGE_HANDLERS.get(message['MsgType'])
            if not message_type:
                continue
            message_handler = getattr(self, '_process_%s_message' % message_type)
            message_handler(message)

    def _process_statusnotify_message(self, message):
        if config.StatusNotifyCode.SYNC_CONV != message['StatusNotifyCode']:
            return
        usernames = message['StatusNotifyUserName'].split(',')
        chatroom_usernames = filter(lambda n: n.startswith('@@') and n not in self.contacts, usernames)
        contacts = self._batch_get_contacts(chatroom_usernames)
        for contact in contacts:
            contact = Contact.from_wx_contact(self, contact)
            self.contacts.add_or_update(contact)

    def send_text(self, content, to_contact):
        message = Message(
            content=content, type=config.MessageType.TEXT.value,
            from_username=self.user.username, to_username=to_contact.username
        )
        return self._send_message(message)

    def _send_message(self, message):
        params = {'pass_ticket': self.pass_ticket}
        data = self._gen_base_request()
        local_id = gen_client_msg_id()
        data.update({
            'Msg': {
                'ClientMsgId': local_id,
                'Content': message.content,
                'FromUserName': message.from_username,
                'ToUserName': message.to_username,
                'LocalID': local_id,
                'Type': message.type
            },
            'Scene': 0
        })
        send_message_api = config.WX_SEND_TEXT_MESSAGE_URL
        res = self.session.post(send_message_api, params=params, json=data)
        return res

    def _gen_base_request(self):
        return {
            'BaseRequest': {
                'DeviceID': self.device_id,
                'Sid': self.sid,
                'Skey': self.skey,
                'Uin': self.uin
            }
        }
