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

from db import DatabaseConnect

conn = DatabaseConnect()


class Activity(object):

    def update_after_login_status(self, param, whereID):
        conditional_query = 'muser_id = %s'

        result = conn.update('m_user', conditional_query, whereID, cti_afterstatus=param)
        # query = conn.query(
        #     "UPDATE m_user SET cti_afterstatus=%s WHERE Server='%s' ", (param, whereID))
        return result
