# coding: utf-8
from __future__ import unicode_literals

from collections import namedtuple

from pywx.utils import (
    is_chatroom, is_mp, is_friend
)


User = namedtuple(
    'User', ('uin', 'username', 'nickname', 'raw')
)


class Contact(object):

    def __init__(self, client, username, sex=0, nickname=None, alias=None,
                 remarkname=None, encry_chatroom_id=None, province=None, city=None):
        self.client = client
        self.username = username
        self.sex = sex
        self.nickname = nickname
        self.alias = alias
        self.remarkname = remarkname
        self.encry_chatroom_id = encry_chatroom_id
        self.province = province
        self.city = city

    @staticmethod
    def from_wx_contact(client, contact):

        def _get_contact_class(contact):
            if is_chatroom(contact):
                return ChatroomContact
            elif is_mp(contact):
                return MPContact
            elif is_friend(contact):
                return FriendContact
            else:
                return SystemContact

        klass = _get_contact_class(contact)
        instance = klass(
            client=client, username=contact['UserName'], sex=contact['Sex'],
            nickname=contact['NickName'], alias=contact['Alias'],
            remarkname=contact['RemarkName'], encry_chatroom_id=contact['EncryChatRoomId'],
            province=contact['Province'], city=contact['City']
        )

        if klass == ChatroomContact:
            for member in contact['MemberList']:
                member = ChatroomMember.from_wx_member(member)
                instance.add_member(member)

        return instance


class FriendContact(Contact):
    pass


class MPContact(Contact):
    pass


class SystemContact(Contact):
    pass


class ChatroomContact(Contact):

    def __init__(self, *args, **kwargs):
        super(ChatroomContact, self).__init__(*args, **kwargs)
        self._members = {}

    @property
    def is_owner(self):
        return self.username == self.client.username

    @property
    def members(self):
        return self._members.values()

    @property
    def strangers(self):
        return filter(lambda m: m.username not in self.client.contacts, self.members)

    def add_member(self, member):
        self._members[member.username] = member

    def remove_member(self, member):
        return self._members.pop(member.username)


class ChatroomMember(object):

    def __init__(self, username, display_name=None, nickname=None):
        self.username = username
        self.display_name = display_name
        self.nickname = nickname

    @classmethod
    def from_wx_member(cls, member):
        return cls(
            username=member['UserName'], display_name=member['DisplayName'],
            nickname=member['NickName']
        )


class ContactSet(object):

    def __init__(self):
        self._contacts = {}

    def __getitem__(self, key):
        return self._contacts.get(key)

    def __contains__(self, key):
        return key in self._contacts

    def __len__(self):
        return len(self._contacts)

    def __iter__(self):
        for contact in self._contacts.values():
            yield contact

    @property
    def chatroooms(self):
        return filter(lambda c: isinstance(c, ChatroomContact), self)

    @property
    def mps(self):
        return filter(lambda c: isinstance(c, MPContact), self)

    @property
    def friends(self):
        return filter(lambda c: isinstance(c, FriendContact), self)

    @property
    def systems(self):
        return filter(lambda c: isinstance(c, SystemContact), self)

    def add_or_update(self, contact):
        self._contacts[contact.username] = contact

    def remove(self, contact):
        return self._contacts.pop(contact.username)
