#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Afvalwijzer
#
# Author: Xorfor
#
# Based on scripts found @:
#   https://gadget-freakz.com/domoticz-dzvents-getgarbagedates-script/
#   https://github.com/Dashticz/dashticz_v2/blob/master/js/garbage.js
#   https://www.mijnafvalwijzer.nl/site/postcodeinfo?LoginForm%5Bpostcode%5D=&postcode=3825AL&isBelgium=&isSpain=&LoginForm%5Bhuisnummer%5D=&huisnummer=41&LoginForm%5Btoevoeging%5D=&toevoeging=&method=getPostcodeInfo
#   https://afvalwijzer.spaarnelanden.nl/rest/adressen/0392200000037848/kalender/2019

"""
<plugin key="xfr_afvalwijzer" name="Afvalwijzer" author="Xorfor" version="1.0.0">
    <params>
        <param field="Mode1" label="Postal code (NL)" width="100px" required="true"/>
        <param field="Mode2" label="House number" width="100px" required="true"/>
        <param field="Mode3" label="Alert days before" width="75px">
            <options>
                <option label="0" value="0" default="true"/>
                <option label="1" value="1"/>
                <option label="2" value="2"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import re
import time
import urllib.request
from datetime import datetime


# Afvalkalender
AKR_URL = "{}/rest/adressen/{}-{}"  # url, postalcode, number => bagid
# BAGID_CAL = "{}/rest/adressen/{}/kalender/{}"  # url, bagid, year
AKR_URLS = [
    {"name": "Afvalvrij/Circulus-Berkel",
        "url": "https://afvalkalender.circulus-berkel.nl"},
    {"name": "Alphen aan den Rijn", "url": "https://afvalkalender.alphenaandenrijn.nl"},
    {"name": "Avalex", "url": "https://www.avalex.nl"},
    {"name": "Berkelland", "url": "https://afvalkalender.gemeenteberkelland.nl"},
    {"name": "Cranendonck", "url": "https://afvalkalender.cranendonck.nl"},
    {"name": "Cure", "url": "https://afvalkalender.cure-afvalbeheer.nl"},
    {"name": "Cyclus NV", "url": "https://afvalkalender.cyclusnv.nl"},
    {"name": "Dar", "url": "https://afvalkalender.dar.nl"},
    {"name": "Den Haag", "url": "https://huisvuilkalender.denhaag.nl"},
    {"name": "GAD", "url": "https://inzamelkalender.gad.nl"},
    {"name": "HVC", "url": "https://apps.hvcgroep.nl"},
    {"name": "Meerlanden", "url": "https://afvalkalender.meerlanden.nl"},
    {"name": "Montfoort", "url": "https://afvalkalender.montfoort.nl"},
    {"name": "RMN", "url": "https://inzamelschema.rmn.nl"},
    {"name": "Spaarnelanden", "url": "https://afvalwijzer.spaarnelanden.nl"},
    {"name": "Súdwest-Fryslân", "url": "https://afvalkalender.sudwestfryslan.nl"},
    {"name": "Venray", "url": "https://afvalkalender.venray.nl"},
    {"name": "Waalre", "url": "http://afvalkalender.waalre.nl"},
    {"name": "ZRD", "url": "https://afvalkalender.zrd.nl"},
]
AKR_ASM_URL = "{}/rest/adressen/{}/afvalstromen"  # url, bagid

# wasteapi.2go-mobile.com


class BasePlugin:

    __DEBUG_NONE = 0
    __DEBUG_ALL = 1

    __HEARTBEATS2MIN = 6
    __MINUTES = 1 * 60 * 4  # every 4 hours

    # Device units
    __UNIT_TEXT = 1
    __UNIT_ALERT = 3
    __UNITS = [
        [__UNIT_TEXT, "Dates", 243, 19],
        [__UNIT_ALERT, "Alert", 243, 22]
    ]

    def __init__(self):
        self.__runAgain = 0

    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Debug(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onDeviceAdded(self, Unit):
        Domoticz.Debug("onDeviceAdded called for Unit " + str(Unit))

    def onDeviceModified(self, Unit):
        Domoticz.Debug("onDeviceModified called for Unit " + str(Unit))

    def onDeviceRemoved(self, Unit):
        Domoticz.Debug("onDeviceRemoved called for Unit " + str(Unit))

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(self.__DEBUG_ALL)
        else:
            Domoticz.Debugging(self.__DEBUG_NONE)
        # Validate parameters
        self._zipcode = re.match("^\d{4}[a-zA-Z]{2}", Parameters["Mode1"])
        self._number = Parameters["Mode2"]
        self._bagid = None
        if self._zipcode:
            self._zipcode = self._zipcode.group()
            Domoticz.Debug("self._zipcode: {}".format(self._zipcode))
            Domoticz.Debug("self._number: {}".format(self._number))
            # Check Afvalkalender: url, postalcode, number => bagid
            for url in AKR_URLS:
                url_bagid = AKR_URL.format(
                    url.get("url"), self._zipcode, self._number)
                # Domoticz.Debug("url_bagid: {}".format(url_bagid))
                try:
                    req = urllib.request.Request(url_bagid)
                    response = urllib.request.urlopen(req).read()
                    data = json.loads(response.decode("utf-8"))
                    self._bagid = data[0].get("bagId")
                    if self._bagid is not None:
                        self._url = url.get("url")
                        break
                except:
                    pass
            Domoticz.Debug("self._bagid: {}".format(self._bagid))
        else:
            Domoticz.Error("Zipcode has a incorrect format. Example: 3564KV")
        if Parameters["Mode3"] is None:
            self._days = 0
        else:
            self._days = int(Parameters["Mode3"])
        # Create devices
        if self._bagid is not None and len(Devices) == 0:
            for unit in self.__UNITS:
                Domoticz.Device(
                    Unit=unit[0], Name=unit[1], Type=unit[2], Subtype=unit[3], Used=1).Create()
        # Log config
        # DumpAllToLog()
        # Connection

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(
            Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.__runAgain -= 1
        if self.__runAgain <= 0:
            self.__runAgain = self.__HEARTBEATS2MIN * self.__MINUTES
            # Execute your command
            if self._bagid is not None:
                dates = Afvalkalender(self._url, self._bagid)
                text = ""
                for date in dates:
                    text += date[0] + ": " + date[1].strftime("%d-%m-%Y\r")
                UpdateDevice(self.__UNIT_TEXT, 0, str(text))
                first_date = list(dates)[:1]
                Domoticz.Debug("first_date: {}".format(first_date))
                for key, value in first_date:
                    date_diff = (value - datetime.now()).days + 1 - self._days
                    # 0 -> 4, 1 -> 3, 2 -> 2, 3 -> 1 , >=4 -> 0
                    level = 4 - max(min(date_diff, 4), 0)
                    UpdateDevice(self.__UNIT_ALERT, level,
                                 "{} ({})".format(key, date_diff))
        else:
            Domoticz.Debug("onHeartbeat called, run again in " +
                           str(self.__runAgain) + " heartbeats.")


def Afvalkalender(url, bagid):
    ophaaldagen = {}
    url_bagid = AKR_ASM_URL.format(url, bagid)
    Domoticz.Debug("Afvalkalender - url_bagid: {}".format(url_bagid))
    try:
        req = urllib.request.Request(url_bagid)
        response = urllib.request.urlopen(req).read()
        data = json.loads(response.decode("utf-8"))
        for stroom in data:
            Domoticz.Debug("ID: {}".format(stroom.get("id")))
            ophaaldatum = stroom.get("ophaaldatum")
            if ophaaldatum is not None:
                Domoticz.Debug("{}: {}".format(
                    ophaaldatum, stroom.get("title")))
                # Bug in Python!!!
                try:
                    datum = datetime.strptime(ophaaldatum, "%Y-%m-%d")
                except TypeError:
                    datum = datetime(
                        *(time.strptime(ophaaldatum, "%Y-%m-%d")[0:6]))
                ophaaldagen[stroom.get("title")] = datum
    except Exception as e:
        Domoticz.Debug("!!! Error: {}".format(e))
    # Sort the dates
    return sorted(ophaaldagen.items(), key=lambda x: x[1])


global _plugin
_plugin = BasePlugin()


def onCommand(Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Color)


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onDeviceAdded(Unit):
    global _plugin
    _plugin.onDeviceAdded(Unit)


def onDeviceModified(Unit):
    global _plugin
    _plugin.onDeviceModified(Unit)


def onDeviceRemoved(Unit):
    global _plugin
    _plugin.onDeviceRemoved(Unit)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status,
                           Priority, Sound, ImageFile)


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


################################################################################
# Generic helper functions
################################################################################
def DumpDevicesToLog():
    # Show devices
    Domoticz.Debug("Device count.........: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device...............: " +
                       str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device Idx...........: " + str(Devices[x].ID))
        Domoticz.Debug("Device Type..........: " +
                       str(Devices[x].Type) + " / " + str(Devices[x].SubType))
        Domoticz.Debug("Device Name..........: '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue........: " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue........: '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device Options.......: '" +
                       str(Devices[x].Options) + "'")
        Domoticz.Debug("Device Used..........: " + str(Devices[x].Used))
        Domoticz.Debug("Device ID............: '" +
                       str(Devices[x].DeviceID) + "'")
        Domoticz.Debug("Device LastLevel.....: " + str(Devices[x].LastLevel))
        Domoticz.Debug("Device Image.........: " + str(Devices[x].Image))


def DumpImagesToLog():
    # Show images
    Domoticz.Debug("Image count..........: " + str(len(Images)))
    for x in Images:
        Domoticz.Debug("Image '" + x + "...': '" + str(Images[x]) + "'")


def DumpParametersToLog():
    # Show parameters
    Domoticz.Debug("Parameters count.....: " + str(len(Parameters)))
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("Parameter '" + x + "'...: '" +
                           str(Parameters[x]) + "'")


def DumpSettingsToLog():
    # Show settings
    Domoticz.Debug("Settings count.......: " + str(len(Settings)))
    for x in Settings:
        Domoticz.Debug("Setting '" + x + "'...: '" + str(Settings[x]) + "'")


def DumpAllToLog():
    DumpDevicesToLog()
    DumpImagesToLog()
    DumpParametersToLog()
    DumpSettingsToLog()


def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details (" + str(len(httpDict)) + "):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug(
                    "....'" + x + " (" + str(len(httpDict[x])) + "):")
                for y in httpDict[x]:
                    Domoticz.Debug("........'" + y + "':'" +
                                   str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("....'" + x + "':'" + str(httpDict[x]) + "'")


def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or Devices[
                Unit].TimedOut != TimedOut or AlwaysUpdate:
            Devices[Unit].Update(
                nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Debug(
                "Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")


def UpdateDeviceOptions(Unit, Options={}):
    if Unit in Devices:
        if Devices[Unit].Options != Options:
            Devices[Unit].Update(nValue=Devices[Unit].nValue,
                                 sValue=Devices[Unit].sValue, Options=Options)
            Domoticz.Debug("Device Options update: " +
                           Devices[Unit].Name + " = " + str(Options))


def UpdateDeviceImage(Unit, Image):
    if Unit in Devices and Image in Images:
        if Devices[Unit].Image != Images[Image].ID:
            Devices[Unit].Update(nValue=Devices[Unit].nValue,
                                 sValue=Devices[Unit].sValue, Image=Images[Image].ID)
            Domoticz.Debug("Device Image update: " +
                           Devices[Unit].Name + " = " + str(Images[Image].ID))
