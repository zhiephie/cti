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
import sys
from collections import OrderedDict


class DatabaseConnect(object):
    _db_connection = None
    _db_cur = None
    # __session = None
    # __connection = None

    def __init__(self):
        self._db_connection = MySQLdb.connect(
            host=config.mysqlhost,
            user=config.mysqluser,
            passwd=config.mysqlpass,
            db=config.mysqldbnm
        )
        self._db_cur = self._db_connection.cursor()
    
    def __del__(self):
        self._db_connection.close()

    def query(self, query, param=None):
        return self._db_cur.execute(query, param)

    def select(self, table, where=None, *args, **kwargs):
        result = None
        query = 'SELECT '
        keys = args
        values = tuple(kwargs.values())
        l = len(keys) - 1

        if keys:
            for i, key in enumerate(keys):
                query += "`" + key + "`"
                if i < l:
                    query += ","
        else:
            query += '*'

        query += 'FROM %s' % table

        if where:
            query += " WHERE %s" % where
        # End if where

        # self.__open()
        self._db_cur.execute(query, values)
        number_rows = self._db_cur.rowcount
        number_columns = len(self._db_cur.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self._db_cur.fetchall()]
        else:
            result = [item[0] for item in self._db_cur.fetchall()]
        # self.__close()

        return result

    def update(self, table, where=None, *args, **kwargs):
        query = "UPDATE %s SET " % table
        keys = kwargs.keys()
        values = tuple(kwargs.values()) + tuple(args)
        l = len(keys) - 1
        for i, key in enumerate(keys):
            query += "`" + key + "` = %s"
            if i < l:
                query += ","
            # End if i less than 1
        # End for keys
        query += " WHERE %s" % where

        # self.__open()
        self._db_cur.execute(query, values)
        self._db_connection.commit()

        # Obtain rows affected
        update_rows = self._db_cur.rowcount
        # self.__close()

        return update_rows

    def insert(self, table, *args, **kwargs):
        values = None
        query = "INSERT INTO %s " % table
        if kwargs:
            keys = kwargs.keys()
            values = tuple(kwargs.values())
            query += "(" + ",".join(["`%s`"] * len(keys)) % tuple(keys) + \
                ") VALUES (" + ",".join(["%s"] * len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"] * len(values)) + ")"

        # self.__open()
        self._db_cur.execute(query, values)
        self._db_connection.commit()
        # self.__close()
        return self._db_cur.lastrowid

    def delete(self, table, where=None, *args):
        query = "DELETE FROM %s" % table
        if where:
            query += ' WHERE %s' % where

        values = tuple(args)

        # self.__open()
        self._db_cur.execute(query, values)
        self._db_connection.commit()

        # Obtain rows affected
        delete_rows = self._db_cur.rowcount
        # self.__close()

        return delete_rows

    def select_advanced(self, sql, *args):
        od = OrderedDict(args)
        query = sql
        values = tuple(od.values())
        # self.__open()
        self._db_cur.execute(query, values)
        number_rows = self._db_cur.rowcount
        number_columns = len(self._db_cur.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self._db_cur.fetchall()]
        else:
            result = [item[0] for item in self._db_cur.fetchall()]

        # self.__close()
        return result

    def version(self):
        self.query("SELECT VERSION()")
        return self._db_cur.fetchone()


# Connect to DB Smartcenter
class DatabaseSmartcenter(object):
    _db_connection = None
    _db_cur = None
    # __session = None
    # __connection = None

    def __init__(self):
        self._db_connection = MySQLdb.connect(
            host=config.smartcenterhost,
            user=config.smartcenteruser,
            passwd=config.smartcenterpass,
            db=config.smartcenterdbnm
        )
        self._db_cur = self._db_connection.cursor()
    
    def __del__(self):
        self._db_connection.close()

    def query(self, query, param=None):
        return self._db_cur.execute(query, param)

    def select(self, table, where=None, *args, **kwargs):
        result = None
        query = 'SELECT '
        keys = args
        values = tuple(kwargs.values())
        l = len(keys) - 1

        if keys:
            for i, key in enumerate(keys):
                query += "`" + key + "`"
                if i < l:
                    query += ","
        else:
            query += '*'

        query += 'FROM %s' % table

        if where:
            query += " WHERE %s" % where
        # End if where

        # self.__open()
        self._db_cur.execute(query, values)
        number_rows = self._db_cur.rowcount
        number_columns = len(self._db_cur.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self._db_cur.fetchall()]
        else:
            result = [item[0] for item in self._db_cur.fetchall()]
        # self.__close()

        return result

    def update(self, table, where=None, *args, **kwargs):
        query = "UPDATE %s SET " % table
        keys = kwargs.keys()
        values = tuple(kwargs.values()) + tuple(args)
        l = len(keys) - 1
        for i, key in enumerate(keys):
            query += "`" + key + "` = %s"
            if i < l:
                query += ","
            # End if i less than 1
        # End for keys
        query += " WHERE %s" % where

        # self.__open()
        self._db_cur.execute(query, values)
        self._db_connection.commit()

        # Obtain rows affected
        update_rows = self._db_cur.rowcount
        # self.__close()

        return update_rows

    def insert(self, table, *args, **kwargs):
        values = None
        query = "INSERT INTO %s " % table
        if kwargs:
            keys = kwargs.keys()
            values = tuple(kwargs.values())
            query += "(" + ",".join(["`%s`"] * len(keys)) % tuple(keys) + \
                ") VALUES (" + ",".join(["%s"] * len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"] * len(values)) + ")"

        # self.__open()
        self._db_cur.execute(query, values)
        self._db_connection.commit()
        # self.__close()
        return self._db_cur.lastrowid

    def delete(self, table, where=None, *args):
        query = "DELETE FROM %s" % table
        if where:
            query += ' WHERE %s' % where

        values = tuple(args)

        # self.__open()
        self._db_cur.execute(query, values)
        self._db_connection.commit()

        # Obtain rows affected
        delete_rows = self._db_cur.rowcount
        # self.__close()

        return delete_rows

    def select_advanced(self, sql, *args):
        od = OrderedDict(args)
        query = sql
        values = tuple(od.values())
        # self.__open()
        self._db_cur.execute(query, values)
        number_rows = self._db_cur.rowcount
        number_columns = len(self._db_cur.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self._db_cur.fetchall()]
        else:
            result = [item[0] for item in self._db_cur.fetchall()]

        # self.__close()
        return result