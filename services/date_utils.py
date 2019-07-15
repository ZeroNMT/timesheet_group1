# -*- coding: utf-8 -*-

from odoo.tools import date_utils
from odoo import fields
import pytz  # pip3 install pytz
import datetime as DT

class  DateUtils():

    def convertString2Datetime(self, strFull):
        strDateTime = strFull[:strFull.find(".")].replace("T", " ")
        dateTime = fields.Datetime.to_datetime(strDateTime)
        strTZ = strFull[-4:]
        if strFull.find("+") == -1:
            dateTime = date_utils.add(dateTime, hours=int(strTZ[:2]), minutes=int(strTZ[2:]))
        else:
            dateTime = date_utils.subtract(dateTime, hours=int(strTZ[:2]), minutes=int(strTZ[2:]))
        return dateTime

    def convertDatetime2String(self, datetime):
        strDatetime = fields.Datetime.to_string(datetime).replace(" ", "T") + ".000" + "+0000"
        return strDatetime

    def convertToLocalTZ(self, datetime, tz=None):
        datetime = DT.datetime.strptime(fields.Datetime.to_string(datetime), '%Y-%m-%d %H:%M:%S')
        datetime_utc = pytz.utc.localize(datetime)
        if tz:
            user_tzInfo = pytz.timezone(tz)
            datetime = datetime_utc.astimezone(user_tzInfo)
        else:
            local_tzInfo = pytz.timezone('Asia/Ho_Chi_Minh')###################
            datetime = datetime_utc.astimezone(local_tzInfo)
        return datetime