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

import config
import MySQLdb


class DatabaseConnect(object):
    _db_connection = None
    _db_cur = None

    def __init__(self):
        self._db_connection = MySQLdb.connect(
            host=config.mysqlhost,
            user=config.mysqluser,
            passwd=config.mysqlpass,
            db=config.mysqldbnm
        )
        self._db_cur = self._db_connection.cursor()

    def query(self, query, param=None):
        return self._db_cur.execute(query, param)

    def version(self):
        self.query("SELECT VERSION()")
        return self._db_cur.fetchone()

    def __del__(self):
        self._db_connection.close()
