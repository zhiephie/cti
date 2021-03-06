#!/usr/bin/env python
#
# Copyright 2017 Wahana Mandiri Syadratama .PT
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Simplified CTI (Computer telephony integration)."""

from __future__ import print_function
import os
import uuid
import json
import re
import struct
import random
import logging as log
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime
import config
from db import DatabaseConnect
from db import DatabaseSmartcenter
from activity import Activity
import constant as const
import MySQLdb
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.tcpclient import TCPClient
import tornado.web
from tornado import websocket
from tornado.util import bytes_type
from tornado.iostream import StreamClosedError
from tornado.options import options

##########################################################################
# Generate Configure Log System
##########################################################################
logger = log.getLogger("WHNSMARCTI")
logger.setLevel(log.INFO)

path = 'log/smartcti.log'
# if os.path.exists(path):
    # with open(path, 'rt') as f:
    # handler = log.FileHandler(path)
# else:
    # open(path, 'w')
# add a rotating handler
handler = RotatingFileHandler(path, maxBytes=100000,
                                backupCount=5)
# handler = log.FileHandler(path)

handler.setLevel(log.INFO)

formatter = log.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Database
conn = DatabaseConnect()
# Database Smartcenter
consmart = DatabaseSmartcenter()
# Activity
activity = Activity()
##########################################################################
# print info start app
##########################################################################
if config.debug:
    print ("[INFO] >> load config local port %s " % (config.localport))
    print ("[INFO] >> load config ATG host %s " % (config.atghost))
    print ("[INFO] >> load config ATG port %s " % (config.atgport))
    print ("[INFO] >> load config AppName  %s " % (config.appInstance))

    print ("[INFO] >> connect to db %s" % (config.mysqldbnm))
    print ("[INFO] >> Database version %s" % (conn.version()))
    # "-----------------------------------------------------------------------------"

print ('[INFO] >> start %s.' % (config.appInstance))
print ('[INFO] >> client listen at port %s ...' % (config.localport))

# Cache this struct definition; important optimization.
int_struct = struct.Struct("<i")
_UNPACK_INT = int_struct.unpack
_PACK_INT = int_struct.pack

MAX_ROOMS = 100
MAX_USERS_PER_ROOM = 100
MAX_LEN_ROOMNAME = 20
MAX_LEN_NICKNAME = 20


class RoomHandler(object):
    """Store data about connections, rooms, which users are in which rooms, etc."""

    def __init__(self):
        # for each client id we'll store  {'wsconn': wsconn, 'room':room,
        # 'nick':nick}
        self.client_info = {}
        # dict  to store a list of  {'cid':cid, 'nick':nick , 'wsconn': wsconn}
        # for each room
        self.room_info = {}
        self.pending_cwsconn = {}  # pending client ws connection
        # store a set for each room, each contains the connections of the
        # clients in the room.
        self.roomates = {}

    def add_roomnick(self, room, nick):
        """Add nick to room. Return generated clientID"""
        # meant to be called from the main handler (page where somebody
        # indicates a nickname and a room to join)
        if len(self.room_info) >= MAX_ROOMS:
            cid = -1
        else:
            if room in self.room_info and len(self.room_info[room]) >= MAX_USERS_PER_ROOM:
                cid = -2
            else:
                roomvalid = re.match(r'[\w-]+$', room)
                nickvalid = re.match(r'[\w-]+$', nick)
                if roomvalid == None:
                    cid = -3
                else:
                    if nickvalid == None:
                        cid = -4
                    else:
                        cid = uuid.uuid4().hex  # generate a client id.
                        if not room in self.room_info:  # it's a new room
                            self.room_info[room] = []
                        c = 1
                        nn = nick
                        nir = self.nicks_in_room(room)
                        while True:
                            if nn in nir:
                                nn = nick + str(c)
                            else:
                                break
                            c += 1
                        self.add_pending(cid, room, nn)

        return cid

    def add_pending(self, cid, room, nick):
        logger.info("| ADD_PENDING |> %s" % cid)
        # we still don't know the WS connection for this client
        self.pending_cwsconn[cid] = {'room': room, 'nick': nick}

    def remove_pending(self, client_id):
        logger.info("| REMOVE_PENDING |> %s" % client_id)
        if client_id in self.pending_cwsconn:
            del(self.pending_cwsconn[client_id])  # no longer pending

    def add_client_wsconn(self, client_id, conn):
        """Store the websocket connection corresponding to an existing client."""

        # add complete client info to the data structures, remove from the
        # pending dict
        self.client_info[client_id] = self.pending_cwsconn[client_id]
        self.client_info[client_id]['wsconn'] = conn
        room = self.pending_cwsconn[client_id]['room']
        nick = self.pending_cwsconn[client_id]['nick']
        self.room_info[room].append(
            {'cid': client_id, 'nick': nick, 'wsconn': conn})
        self.remove_pending(client_id)
        cid_room = self.client_info[client_id]['room']
        if cid_room in self.roomates:
            self.roomates[cid_room].add(conn)
        else:
            self.roomates[cid_room] = {conn}

        for user in self.room_info[cid_room]:
            if user['cid'] == client_id:
                user['wsconn'] = conn
                break

        # send "join" and and "nick_list" messages
        self.send_join_msg(client_id)
        nick_list = self.nicks_in_room(room)
        cwsconns = self.roomate_cwsconns(client_id)
        self.send_nicks_msg(cwsconns, nick_list)

    def remove_client(self, client_id):
        """Remove all client information from the room handler."""
        cid_room = self.client_info[client_id]['room']
        nick = self.client_info[client_id]['nick']
        # first, remove the client connection from the corresponding room in
        # self.roomates
        client_conn = self.client_info[client_id]['wsconn']
        if client_conn in self.roomates[cid_room]:
            self.roomates[cid_room].remove(client_conn)
            if len(self.roomates[cid_room]) == 0:
                del(self.roomates[cid_room])
        r_cwsconns = self.roomate_cwsconns(client_id)
        # filter out the list of connections r_cwsconns to remove clientID
        r_cwsconns = [conn for conn in r_cwsconns if conn !=
                      self.client_info[client_id]['wsconn']]
        self.client_info[client_id] = None
        for user in self.room_info[cid_room]:
            if user['cid'] == client_id:
                self.room_info[cid_room].remove(user)
                break
        self.send_leave_msg(nick, r_cwsconns)
        nick_list = self.nicks_in_room(cid_room)
        self.send_nicks_msg(r_cwsconns, nick_list)
        if len(self.room_info[cid_room]) == 0:  # if room is empty, remove.
            del(self.room_info[cid_room])
            logger.info("| ROOM_REMOVED |> %s" % cid_room)

    def nicks_in_room(self, rn):
        """Return a list with the nicknames of the users currently connected to the specified room."""
        nir = []  # nicks in room
        for user in self.room_info[rn]:
            nir.append(user['nick'])
        return nir

    def roomate_cwsconns(self, cid):
        """Return a list with the connections of the users currently connected to the room where
        the specified client (cid) is connected."""
        cid_room = self.client_info[cid]['room']
        r = []
        if cid_room in self.roomates:
            r = self.roomates[cid_room]
        return r

    def send_join_msg(self, client_id):
        """Send a message of type 'join' to all users connected to the room where client_id is connected."""
        nick = self.client_info[client_id]['nick']
        r_cwsconns = self.roomate_cwsconns(client_id)
        msg = {"msgtype": "join", "username": nick,
               "payload": " joined the chat room."}
        pmessage = json.dumps(msg)
        for conn in r_cwsconns:
            conn.write_message(pmessage)

    @staticmethod
    def send_nicks_msg(conns, nick_list):
        """Send a message of type 'nick_list' (contains a list of nicknames) to all the specified connections."""
        msg = {"msgtype": "nick_list", "payload": nick_list}
        pmessage = json.dumps(msg)
        for c in conns:
            c.write_message(pmessage)

    @staticmethod
    def send_leave_msg(nick, rconns):
        """Send a message of type 'leave', specifying the nickname that is leaving, to all the specified connections."""
        msg = {"msgtype": "leave", "username": nick,
               "payload": " left the chat room."}
        pmessage = json.dumps(msg)
        for conn in rconns:
            conn.write_message(pmessage)


class MainHandler(tornado.web.RequestHandler):

    def initialize(self, room_handler):
        """Store a reference to the "external" RoomHandler instance"""
        self.__rh = room_handler

    def get(self, action=None):
        """Render cticlient.php if required arguments are present, render main.html otherwise."""
        if not action:  # init startup sequence, won't be completed until the websocket connection is established.
            try:
                room = self.get_argument("room")
                nick = self.get_argument("nick")
                # this alreay calls add_pending
                cid = self.__rh.add_roomnick(room, nick)
                self.set_cookie("ftc_cid", cid)
                self.set_cookie("ftc_agentid", room)
                consmart.query(
                    "SELECT tot_busy_time, tot_ring_time, tot_talk_time FROM agent_activity WHERE agent = %s", ([room]))
                if consmart._db_cur.rowcount:
                    r = consmart._db_cur.fetchone()
    
                    self.set_cookie("busy_time_" + room, str(r[0]))
                    self.set_cookie("ring_time_" + room, str(r[1]))
                    self.set_cookie("talk_time_" + room, str(r[2]))

                emsgs = ["The nickname provided was invalid. It can only contain letters, numbers, - and _.\nPlease try again.",
                         "The room name provided was invalid. It can only contain letters, numbers, - and _.\nPlease try again.",
                         "The maximum number of users in this room (%d) has been reached.\n\nPlease try again later." % MAX_USERS_PER_ROOM,
                         "The maximum number of rooms (%d) has been reached.\n\nPlease try again later." % MAX_ROOMS]
                if cid == -1 or cid == -2:
                    self.render("maxreached.html", emsg=emsgs[cid])
                else:
                    if cid < -2:
                        self.render("main.php", emsg=emsgs[cid])
                    else:
                        self.render("cticlient.php", room_name=room)
                        # self.render("templates/chat.html", room_name=room)
            except tornado.web.MissingArgumentError:
                self.render("main.php", emsg="")
        else:
            # drop client from "pending" list. Client cannot establish WS
            # connection.
            if action == "drop":
                client_id = self.get_cookie("ftc_cid")
                if client_id:
                    self.__rh.remove_pending(client_id)
                    self.render("templates/nows.html")


class ClientWSConnection(websocket.WebSocketHandler):

    def initialize(self, room_handler):
        """Store a reference to the "external" RoomHandler instance"""
        self.__rh = room_handler
        self.atg_stream = None
        self.atg = TCPClient()
        IOLoop.current().spawn_callback(self.atg_connect)

    def open(self):
        self.__clientID = self.get_cookie("ftc_cid")
        self.__agentID = self.get_cookie("ftc_agentid")
        self.__agentClient = self.get_cookie("cookie_id")
        self.__ext = self.get_cookie("ext_number")
        self.__vdn_group = self.get_cookie("vdn_group")
        self.__ip_address = self.get_cookie("ip_address")
        self.__today = datetime.now().replace(microsecond=0)
        self.__rh.add_client_wsconn(self.__clientID, self)
        logger.info("| WS_OPENED |> %s" % self.__clientID)

    def on_message(self, message):
        msg = json.loads(message)
        mlen = len(msg['payload'])
        msg['username'] = self.__rh.client_info[self.__clientID]['nick']

        """Update After Status"""
        conn.update('m_user', 'muser_id = %s',
                    msg['userid'], cti_afterstatus=msg['after'])

        after = str(msg['after'])
        callno = msg['callno']
        busy = msg['busy']
        ringtone = msg['ring']

        try:
            conn.query(
                "SELECT cti_agentpabx, cti_password, cti_extension, cti_afterstatus, cti_agent_group FROM m_user WHERE muser_id = %s", ([
                                                                                                                                        self.__agentClient])
            )

            for i in range(conn._db_cur.rowcount):
                row = conn._db_cur.fetchone()
                consmart.query(
                    "SELECT vdn FROM vdn_agent_group WHERE agent_group = %s", ([row[4]]))
                row_smart = consmart._db_cur.fetchone()
                pabx_agent = row[0]
                pabx_pass = row[1]
                pabx_ext = row[2]
                pabx_afsta = row[3]
                pabx_vdn = row_smart[0]
        except MySQLdb.Error:
            print ("Error %d: %s" % (e.args[0], e.args[1]))
            sys.exit(1)

        varcommand = msg['payload']

        if varcommand == 'login':
            msg_do_login = self.__agentClient + ';do_user_login;' + \
                pabx_agent + ';' + pabx_pass + ';' + pabx_ext + ';' + pabx_vdn
            self.atg_stream.write((msg_do_login).encode())
            logger.info("| MSG-CTI |> Login device %s" % (msg_do_login))

            msg_do_run_device = pabx_ext + ';do_run_device'
            self.atg_stream.write((msg_do_run_device).encode())
            logger.info("| MSG-CTI |> Run device %s" % (msg_do_run_device))

        elif varcommand == 'retrieve':
            msg_retrieve = self.__agentClient + ';do_dev_retrieve_call'
            self.atg_stream.write((msg_retrieve).encode())
            logger.info("| MSG-CTI  |> Retrieve Call %s" % (msg_retrieve))

        elif varcommand == 'answer':
            msg_answer = self.__agentClient + ';do_dev_answer_call'
            self.atg_stream.write((msg_answer).encode())
            logger.info("| MSG-CTI  |> Answer Call %s" % (msg_answer))

        elif varcommand == 'hangup':
            msg_hangup = pabx_ext + ';do_dev_hangup_call'
            self.atg_stream.write((msg_hangup).encode())
            logger.info("| MSG-CTI  |> Hangup Call %s" % (msg_hangup))

        elif varcommand == 'loginagent':
            msg_acd_login = self.__agentClient + ';do_ag_login;' + pabx_ext + \
                ';' + pabx_agent + ';' + pabx_pass + ';' + pabx_afsta
            self.atg_stream.write((msg_acd_login).encode())
            logger.info("| MSG-CTI  |> ACD Login %s" % (msg_acd_login))

        elif varcommand == 'ready':
            msg_acd_ready = self.__agentClient + ';do_ag_ready;' + \
                pabx_ext + ';' + pabx_agent + ';' + pabx_pass + \
                ';' + pabx_afsta
            self.atg_stream.write((msg_acd_ready).encode())
            logger.info("| MSG-CTI |> Ready %s" % (msg_acd_ready))

        elif varcommand == 'notready':
            msg_acd_not_ready = self.__agentClient + ';do_ag_aux;' + \
                pabx_ext + ';' + pabx_agent + ';' + pabx_pass + \
                ';' + after
            self.atg_stream.write((msg_acd_not_ready).encode())
            logger.info("| MSG-CTI |> Not Ready %s" % (msg_acd_not_ready))

        elif varcommand == 'logout':
            msg_acd_shutdown = self.__agentClient + ';do_ag_logout;' + \
                pabx_ext + ';' + pabx_agent + ';' + pabx_pass + \
                ';' + pabx_afsta
            self.atg_stream.write((msg_acd_shutdown).encode())
            logger.info("| MSG-CTI |> Logout %s" % (msg_acd_shutdown))

            msg_do_shutdown = pabx_ext + ';do_user_shutdown'
            self.atg_stream.write((msg_do_shutdown).encode())
            logger.info("| MSG-CTI |> Shutdown %s" % (msg_do_shutdown))

        elif varcommand == 'makecall':
            msg_do_make_call = self.__agentClient + ';do_dev_make_call;' + callno
            self.atg_stream.write((msg_do_make_call).encode())
            logger.info("| MSG-CTI |> Make Call %s" % (msg_do_make_call))

        elif varcommand == 'busy':
            dt = datetime.now().replace(microsecond=0)
            if busy < 1:
                busy = 0
            
            consmart.query(
                "SELECT tot_acd_call, tot_abd_call FROM agent_activity where agent = %s", ([self.__agentID]))
            if consmart._db_cur.rowcount:
                rr = consmart._db_cur.fetchone()
                if ringtone == 'busy':
                    consmart.query(
                        'UPDATE call_session SET last_status=status, status=3011 WHERE session_id = %s', ([self.__agentID]))
                    consmart.update('agent_activity', 'agent = %s',
                                    self.__agentID, tot_busy_time=busy)
                elif ringtone == 'ring':
                    consmart.update('agent_activity', 'agent = %s',
                                    self.__agentID, tot_ring_time=busy)
                    consmart.query('UPDATE call_session SET last_status=status, status=3004, direction = 1, \
                        agent_time=now(), agent_ring = now() - agent_ring_time \
						WHERE session_id = %s', ([self.__clientID]))
                elif ringtone == 'talk':
                    consmart.update('agent_activity', 'agent = %s',
                                    self.__agentID, tot_talk_time=busy)
                elif ringtone == 'acd':
                    acd_call = int(busy) + int(rr[0])
                    consmart.update('agent_activity', 'agent = %s',
                                    self.__agentID, tot_acd_call=acd_call)
                elif ringtone == 'abd':
                    abd_call = int(busy) + int(rr[1])
                    consmart.update('agent_activity', 'agent = %s',
                                    self.__agentID, tot_abd_call=abd_call)
                elif ringtone == 'aux':
                    logger.info("EVENTLOGGER>> Agent Not Ready")
                    activity.dblog_AgentActivity(
                        self.__agentID, 3, self.__vdn_group,
                        dt, self.__ext, busy, self.__ip_address
                    )
                #"""Start Call Session"""
                elif ringtone == 'offered':
                    consmart.query(
                        'SELECT session_id FROM call_session WHERE session_id = %s', ([self.__clientID]))
                    if consmart._db_cur.rowcount < 1:
                        consmart.insert('call_session', session_id=self.__clientID, direction=1, status=3002,
                                        start_time=dt, a_number=busy, b_number=self.__ext, d_number=0,
                                        agent_id=self.__agentID, agent_group=self.__vdn_group,
                                        agent_ring_time=datetime.now().replace(microsecond=0),
                                        agent_time=datetime.now().replace(microsecond=0), agent_ext=self.__ext
                                        )

                    consmart.query('UPDATE call_session SET last_status=status, status=3002, agent_id = %s, \
                        agent_group=%s, agent_ext=%s, agent_ring_time=now(), ivr_duration = now() - start_time \
						WHERE session_id = %s', (self.__agentID, self.__vdn_group, self.__ext, [self.__clientID]))

                elif ringtone == 'hold':
                    consmart.query(
                        'UPDATE call_session SET agent_hold = unix_timestamp(now()) WHERE session_id = %s', ([self.__clientID]))

                elif ringtone == 'retrieve':
                    consmart.query(
                        'UPDATE call_session SET agent_hold = unix_timestamp(now()) - agent_hold WHERE session_id = %s', ([self.__clientID]))

                elif ringtone == 'disconnect':
                    consmart.query("UPDATE call_session SET last_status=status, end_time=now(), status=3005, agent_end_time = now(), \
                        agent_talk = unix_timestamp(now()) - unix_timestamp(agent_time), \
					    ivr_duration = unix_timestamp(agent_ring_time) - unix_timestamp(start_time) WHERE session_id = %s", ([self.__clientID]))

                elif ringtone == 'originated':
                    consmart.query(
                        'UPDATE call_session SET last_status=status, status=3007, b_number=%s WHERE session_id = %s', (busy, [self.__clientID]))

                elif ringtone == 'init':
                    consmart.query(
                        'SELECT session_id FROM call_session WHERE session_id = %s', ([self.__clientID]))
                    if consmart._db_cur.rowcount < 1:
                        consmart.insert('call_session', session_id=self.__clientID, direction=2, status=3009,
                                        start_time=dt, a_number=self.__ext, agent_id=self.__agentID,
                                        agent_group=self.__vdn_group, agent_time=datetime.now().replace(microsecond=0),
                                        agent_ext=self.__ext
                                        )

    def on_close(self):
        cid = self.__clientID
        self.__rh.remove_client(self.__clientID)
        logger.info("| WS_CLOSED |> %s" % cid)

    def make_frame(self, message):
        opcode = 0x1  # we know that binary is false, so opcode is s1
        message = tornado.escape.utf8(message)
        assert isinstance(message, bytes_type)
        finbit = 0x80
        mask_bit = 0
        frame = struct.pack("B", finbit | opcode)
        l = len(message)
        if l < 126:
            frame += struct.pack("B", l | mask_bit)
        elif l <= 0xFFFF:
            frame += struct.pack("!BH", 126 | mask_bit, l)
        else:
            frame += struct.pack("!BQ", 127 | mask_bit, l)
        frame += message
        return frame

    def write_frame(self, frame):
        try:
            #self._write_frame(True, opcode, message)
            self.stream.write(frame)
        except StreamClosedError:
            pass
            # self._abort()

    def allow_draft76(self):
        return True

    @gen.coroutine
    def atg_connect(self):
        while True:
            try:
                self.atg_stream = yield self.atg.connect(config.atghost, config.atgport)
                logger.info("Spawn ATG Connected at port %d", config.atgport)
                # Set TCP_NODELAY / disable Nagle's Algorithm.
                self.atg_stream.set_nodelay(True)
                while True:
                    # line = yield self.atg_stream.read_bytes(1024, partial=True)
                    # OR
                    line = yield self.atg_stream.read_until(b"\n")
                    logger.info("| RES-CTI |>  %s" % line.decode().strip())
                    logger.info("| MSG-RECEIVED |> %s" % self.__clientID)
                    rconns = self.__rh.roomate_cwsconns(self.__clientID)
                    frame = self.make_frame(line.decode().strip())
                    for conn in rconns:
                        conn.write_frame(frame)
                    # yield gen.sleep(random.random() * 10)
                    # yield gen.sleep(0.01)
                    # n = line.decode().strip().split(";")[-1:]
                    # ext = line.decode().strip().split(";", 1)[0]
                    atg_codes = line.decode().strip().split(';')
                    if 2 in range(len(atg_codes)):
                        # atg_code = line.decode().strip().split(";", 2)[1]
                        atg_code = atg_codes[1]
                        dt = datetime.now().replace(microsecond=0)

                        if int(atg_code) == const.CM_CTI_USER_LOGIN:
                            logger.info("EVENTLOGGER>> Agent Login")
                            activity.dblog_AgentLogin(
                                self.__agentID, 1, self.__vdn_group,
                                dt, self.__ext, 0, 0, 0, self.__ip_address
                            )

                        elif int(atg_code) == const.CM_DEV_AG_READY:
                            logger.info("EVENTLOGGER>> Agent Ready")
                            activity.dblog_AgentActivity(
                                self.__agentID, 2, self.__vdn_group,
                                dt, self.__ext, self.__ip_address
                            )

                        elif int(atg_code) == const.CM_DEV_AG_LOGOUT:
                            logger.info("EVENTLOGGER>> Agent Logout")
                            activity.dblog_LogAgentLogout(
                                self.__agentID, dt, self.__ip_address,
                                self.__vdn_group, 0, self.__ext
                            )

                        elif int(atg_code) == const.EV_DEV_INITIATED:
                            logger.info("EVENTLOGGER>> Agent Call Intitial")
                            activity.dblog_LogAgentInit(self.__agentID, dt)

                        elif int(atg_code) == const.EV_DEV_CON_CLEAR:
                            logger.info("EVENTLOGGER>> Agent Call On Clear")
                            activity.dblog_LogAgentOnClear(self.__agentID, dt)

                        elif int(atg_code) == const.EV_DEV_DELIVERED:
                            logger.info("EVENTLOGGER>> Agent Call Offered")
                            activity.dblog_LogAgentOffered(self.__agentID, dt)

                        elif int(atg_code) == const.EV_DEV_ESTABLISHED:
                            logger.info("EVENTLOGGER>> Agent Call Connected")
                            activity.dblog_LogAgentConnected(
                                self.__agentID, dt)

                        elif int(atg_code) == const.EV_DEV_HELD:
                            logger.info("EVENTLOGGER>> Agent Call Hold")
                            activity.dblog_LogAgentHold(self.__agentID, dt)

                        elif int(atg_code) == const.EV_DEV_RETRIEVED:
                            logger.info("EVENTLOGGER>> Agent Call Retrive")
                            activity.dblog_LogAgentRetrive(self.__agentID, dt)

                    yield gen.sleep(0.5)
            except StreamClosedError as exc:
                logger.error("Error connecting to %d: %s", config.atgport, exc)
                yield gen.sleep(5)
                # pass


class Application(tornado.web.Application):
    def __init__(self):
        rh = RoomHandler()
        handlers = [
            (r"/(|drop)", MainHandler, {'room_handler': rh}),
            (r"/ws", ClientWSConnection, {'room_handler': rh})
        ]
        settings = dict(
            cookie_secret="PURWANTO",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            # xsrf_cookies=True,
            debug=config.debug,
        )
        super(Application, self).__init__(handlers, **settings)


def main():
    options.parse_command_line()
    app = Application()
    app.listen(config.localport)
    IOLoop.instance().start()
