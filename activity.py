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

from db import DatabaseSmartcenter
from datetime import datetime
import time

conn = DatabaseSmartcenter()


class Activity(object):

    def __init__(self):
        # self.today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.today = datetime.now().replace(microsecond=0)

    """Done and Check"""

    def dblog_AgentActivity(self, agentid, status, *args):
        keys = list(args)
        if 4 in range(len(keys)):
            status_reason = keys[3]
            ip_address = keys[4]
        else:
            status_reason = 0
            ip_address = keys[3]

        conn.query(
            "SELECT id, status_time, tot_ready_time, status, tot_notready_time, tot_acw_time, tot_acd_call FROM agent_activity WHERE agent = %s", [agentid])

        if conn._db_cur.rowcount:
            row = conn._db_cur.fetchone()
            now = datetime.now().replace(microsecond=0)
            time_stt = row[1]
            tdelta = now - time_stt

            self.dblog_LogAgentHistory(
                agentid, status, status_reason, ip_address, keys)

            sec = self.get_sec(str(tdelta))

            if status == 2:
                # Ready
                second_ready = int(sec) + int(row[2])
                second_noready = row[4]

            elif status == 3:
                # Not Ready
                second_ready = row[2]
                second_noready = int(sec) + int(row[4])

            conn.update('agent_activity', 'agent = %s', agentid,
                        agent_group=keys[0], status=status, status_time=keys[1],
                        login_time=keys[1], logout_time=None, ext_number=keys[2],
                        location=ip_address, last_logout_time=keys[1], tot_ready_time=second_ready,
                        tot_notready_time=second_noready, tot_acw_time=0, status_reason=status_reason
                        )

    """Done and Check"""

    def dblog_AgentLogin(self, agentid, status, *args):
        keys = list(args)
        now = time.strftime('%Y-%m-%d')
        conn.query(
            "SELECT id, logout FROM agent_activity WHERE agent = %s", [agentid])
        if conn._db_cur.rowcount:
            row = conn._db_cur.fetchone()
            if row[1] > 0:
                conn.update('agent_activity', 'agent = %s', agentid,
                            agent_group=keys[0], status=status, status_time=keys[1],
                            login_time=self.today, logout_time=None, ext_number=keys[2],
                            location=keys[6], last_login_time=self.today, last_logout_time=None,
                            tot_ready_time=keys[3], tot_notready_time=keys[4],
                            tot_acw_time=keys[5], status_reason=0, logout=0
                            )
        else:
            conn.insert('agent_activity', agent=agentid, agent_group=keys[0], status=status, status_time=keys[1],
                        login_time=self.today, logout_time=None, ext_number=keys[2],
                        location=keys[6]
                        )

        self.dblog_LogAgentHistory(agentid, status, 0, keys[6], keys)

    def dblog_DataCallInitiated(self, session_id, agentid, *args):
        key = list(args)
        conn.insert('call_session', session_id=session_id, agent_id=agentid,
                    direction=key[0], status=key[1], start_time=self.today,
                    a_number=key[3], agent_group=key[4], agent_time=self.today,
                    agent_ext=key[5], assign_id=key[6]
                    )

    def dblog_LogAgentHistory(self, agentid, status, rea, ip, keys):
        # if 3 in range(len(keys)):
        #     reason = keys[3]
        # else:
        #     reason = rea
        # Update status sebelumnya
        condition = 'end_time is NULL and agent = %s'
        conn.update('agent_activity_log', condition, agentid,
                    end_time=self.today, next_status=status, next_reason=rea
                    )

        conn.insert('agent_activity_log', agent=agentid, agent_group=keys[0],
                    ext_number=keys[2], location=ip, start_time=self.today,
                    status=status, reason=rea
                    )

    def dblog_LogAgentLogout(self, agentid, dt, ip, *args):
        conn.update('agent_activity', 'agent = %s', agentid,
                    status=0, logout_time=dt, last_logout_time=dt, logout=1
                    )
        keys = list(args)
        self.dblog_LogAgentHistory(agentid, 0, 0, ip, keys)

    def dblog_LogAgentOnClear(self, agentid, dt):
        conn.update('agent_activity', 'agent = %s', agentid, ext_status=25)

    def dblog_LogAgentOffered(self, agentid, dt):
        conn.update('agent_activity', 'agent = %s', agentid, ext_status=26)

    def dblog_LogAgentConnected(self, agentid, dt):
        conn.update('agent_activity', 'agent = %s', agentid, ext_status=27)

    def dblog_LogAgentHold(self, agentid, dt):
        conn.update('agent_activity', 'agent = %s', agentid, ext_status=28)

    def dblog_LogAgentRetrive(self, agentid, dt):
        conn.update('agent_activity', 'agent = %s', agentid, ext_status=29)

    def dblog_LogAgentInit(self, agentid, dt):
        conn.update('agent_activity', 'agent = %s', agentid, ext_status=30)

    @staticmethod
    def get_sec(time_str):
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)
