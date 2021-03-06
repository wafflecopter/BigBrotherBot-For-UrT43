# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

__version__ = '0.1'
__author__  = 'isopropanol'

import b3
import b3.cron
import b3.events
import b3.plugin
import os
import random
import re
import requests
import string
import thread
import time

from b3.functions import getCmd
from ConfigParser import NoOptionError


class VpncheckPlugin(b3.plugin.Plugin):
    # requiresConfigFile = True
    # requiresPlugins = ['admin']
    _adminPlugin = None
    _immunity_level = None
    # required params (if left empty it will not do that check)
    _key_iphub = None
    _key_abuseipdb = None
    _email_address_getipintel = None
    # optional params
    _days_abuseipdb = 30
    _score_needed_abuseipdb = 50
    _score_needed_getipintel = 0.94
    _on_connect = 0
    _whitelists = None

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        startup the plugin
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = getCmd(self, cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        self.registerEvent('EVT_CLIENT_AUTH', self.onPlayerConnect)

        if self._whitelists:
            for whitelist in self._whitelists:
                if whitelist._cronTab:
                    # remove existing crontab
                    self.console.cron - whitelist._cronTab

    def onLoadConfig(self):
        """
        load plugin configuration
        """
        try:
            self._immunity_level = self.config.getint('settings', 'immunity_level')
        except (NoOptionError, ValueError):
            self._immunity_level = 100

        self.debug('immunity level : %s' % self._immunity_level)
        # self.checkConnectedPlayers()

        try:
            self._key_iphub = self.config.get('settings', 'key_iphub')
            self.debug('loaded settings/key_iphub: %s' % self._key_iphub)
        except NoOptionError:
            self.error('could not find settings/key_iphub in config file')
        except KeyError, e:
            self.error('could not load settings/key_iphub config value: %s' % e)

        try:
            self._key_abuseipdb = self.config.get('settings', 'key_abuseipdb')
            self.debug('loaded settings/key_abuseipdb: %s' % self._key_abuseipdb)
        except NoOptionError:
            self.error('could not find settings/key_abuseipdb in config file')
        except KeyError, e:
            self.error('could not load settings/key_abuseipdb config value: %s' % e)

        try:
            self._email_address_getipintel = self.config.get('settings', 'email_address_getipintel')
            self.debug('loaded settings/email_address_getipintel: %s' % self._email_address_getipintel)
        except NoOptionError:
            self.error('could not find settings/email_address_getipintel in config file')
        except KeyError, e:
            self.error('could not load settings/email_address_getipintel config value: %s' % e)

        try:
            self._days_abuseipdb = self.config.getint('settings', 'days_abuseipdb')
            self.debug('loaded settings/days_abuseipdb: %s' % self._days_abuseipdb)
        except NoOptionError:
            self.warning('could not find settings/days_abuseipdb in config file, '
                         'using default: %s' % self._days_abuseipdb)
        except KeyError, e:
            self.error('could not load settings/days_abuseipdb config value: %s' % e)
            self.debug('using default value (%s) for settings/days_abuseipdb' % self._days_abuseipdb)

        try:
            self._score_needed_abuseipdb = self.config.getint('settings', 'score_needed_abuseipdb')
            self.debug('loaded settings/score_needed_abuseipdb: %s' % self._score_needed_abuseipdb)
        except NoOptionError:
            self.warning('could not find settings/score_needed_abuseipdb in config file, '
                         'using default: %s' % self._score_needed_abuseipdb)
        except KeyError, e:
            self.error('could not load settings/score_needed_abuseipdb config value: %s' % e)
            self.debug('using default value (%s) for settings/score_needed_abuseipdb' % self._score_needed_abuseipdb)

        try:
            self._score_needed_getipintel = self.config.getfloat('settings', 'score_needed_getipintel')
            self.debug('loaded settings/score_needed_getipintel: %s' % self._score_needed_getipintel)
        except NoOptionError:
            self.warning('could not find settings/score_needed_getipintel in config file, '
                         'using default: %s' % self._score_needed_getipintel)
        except KeyError, e:
            self.error('could not load settings/score_needed_getipintel config value: %s' % e)
            self.debug('using default value (%s) for settings/score_needed_getipintel' % self._score_needed_getipintel)

        try:
            self._on_connect = self.config.getint('settings', 'on_connect')
            self.debug('loaded settings/on_connect: %s' % self._on_connect)
        except NoOptionError:
            self.warning('could not find settings/on_connect in config file, '
                         'using default: %s' % self._on_connect)
        except KeyError, e:
            self.error('could not load settings/on_connect config value: %s' % e)
            self.debug('using default value (%s) for settings/on_connect' % self._on_connect)

        # load whitelists from config (using banlist object here)
        self._whitelists = []
        for whitelistconfig in self.config.get('ip_whitelist'):
            try:
                lst = IpBanlist(self, whitelistconfig)
                self._whitelists.append(lst)
                self.info("IP white list [%s] loaded" % lst.name)
            except Exception, e:
                self.error(e)
        self.debug("VPNCheck %d whitelists loaded" % len(self._whitelists))

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onPlayerConnect(self, event):
        """
        Examine players ip address and allow/deny connection.
        """
        # self.debug("VPNCheck: onPlayerConnect")
        if self._on_connect == 1:
            if self._whitelists:
                # self.debug("DK: running check")
                thread.start_new_thread(self.checkClient, (event.client,))

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def checkClient(self, client):
        # self.debug("DK: checkClient")
        # check the level of the connecting client before applying the filters
        if client.maxLevel >= self._immunity_level:
            self.info('VPNCheck: %s is a high enough level user and allowed to connect. client: %s; immunity: %s' %
                      (client.name, client.maxLevel, self._immunity_level))
        else:
            self.debug("VPNCheck: checkClient %s" % client.name)
            # check whitelist
            for whitelist in self._whitelists:
                result = whitelist.isBanned(client)
                if result is not False:
                    self.debug('VPNCheck %s %s, ip:%s, guid:%s. Found in whitelist : %s' % (client.id, client.name
                                                                                            , client.ip, client.guid
                                                                                            , whitelist.name))
                    msg = whitelist.getMessage(client)
                    if msg and msg != "":
                        self.console.write(msg)
                    return

            self.debug("DK: checking for vpn")
            # if not whitelisted then check for vpn
            _is_vpn_getipintel = False
            if self._email_address_getipintel and self._email_address_getipintel != "blank":
                _is_vpn_getipintel = self.CheckGetIPIntel(client.ip, self._email_address_getipintel,
                                                          self._score_needed_getipintel)
                self.debug("VPNCheck on_connect for %s [%s]: %s", (client.name, client.ip, _is_vpn_getipintel))
                if _is_vpn_getipintel:
                    self.debug("VPNCheck: kicking %s" % client.name)
                    client.kick('VPN/Proxy detected [%s]' % client.name, keyword="vpncheck", silent=True)

    def CheckIPHub(self, _userip, _key_iphub):
        _is_vpn_iphub = False
        isp = ""
        countryCode = ""

        # API documentation URL: https://iphub.info/api

        ## old: http://legacy.iphub.info/api.php?ip=136.57.192.102&showtype=4
        ## web 2019-05-13: https://iphub.info/?ip=136.57.192.102
        ## api 2019-05-13: http://v2.api.iphub.info/ip/8.8.8.8 -H "X-Key: 123"

        # make the request
        url = "http://v2.api.iphub.info/ip/" + _userip
        headers = {"X-Key": _key_iphub}
        try:
            request = requests.get(url, headers=headers)
        except requests.exceptions.SSLError:
            self.error("SSLError connecting to %s", url)
            return _is_vpn_iphub, isp

        # DEBUG: show what came back
        # request: < Response[200] >
        # encoding: UTF-8
        # headers: {'Server': 'nginx', 'Date': 'Mon, 13 May 2019 21:42:23 GMT', 'Content-Type': 'application/json; charset=UTF-8', 'Content-Length': '137', 'Connection': 'keep-alive', 'X-Ratelimit-Limit': '1000', 'X-Ratelimit-Remaining': '992', 'X-Ratelimit-Reset': '1557861520'}
        # content: b'{'ip': '123.45.67.89', 'countryCode': 'US', 'countryName': 'United States', 'asn': 11511, 'isp': 'GOOGLE-FIBER', 'block': 0, 'hostname': '123.45.67.89'}'
        # print(request)
        # print(request.encoding)
        # print(request.headers)
        # print(request.content)

        # DEBUG test data
        # data = {'ip': '123.45.67.89', 'countryCode': 'US', 'countryName': 'United States', 'asn': 11511, 'isp': 'GOOGLE-FIBER', 'block': 0, 'hostname': '123.45.67.89'}
        # _data = json.dumps(_data)
        # print(_data)

        # parse the data
        try:
            data = request.json()
        except ValueError:
            self.warn("got non-json response from %s", url)
            return _is_vpn_iphub, isp

        # print(data)

        # sort_keys: True for "pretty display"
        # print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

        # print(data["block"])

        try:
            if data["block"] == "1":
                _is_vpn_iphub = True
        except KeyError:
            self.warn("key not found: block")

        try:
            isp = data["isp"]
        except KeyError:
            self.warn("key not found: isp")

        try:
            countryCode = data["countryCode"]
        except KeyError:
            self.warn("key not found: countryCode")

        return _is_vpn_iphub, isp, countryCode

    def CheckAbuseIPDB(self, _userip, _key_abuseipdb, _days_abuseipdb, _score_needed_abuseipdb=91):
        _is_vpn_abuseipdb = False
        domain = ""
        isp = ""
        countryCode = ""
        # API documentation URL: https://docs.abuseipdb.com/#check-endpoint
        # OLD _request = "https://www.abuseipdb.com/check/%s/json?key=%s&days=%s" % (_userip, _key_abuseipdb, _days_abuseipdb)
        # 2019-05-13
        # 'https://api.abuseipdb.com/api/v2/check?ipAddress=' ipAddress\
        # - H 'Accept: application/json' \
        # - H 'Key: <abuseipdb_apikey>' \

        # make the request
        url = "https://api.abuseipdb.com/api/v2/check?ipAddress=" + _userip
        headers = {"Accept": "application/json", "Key": _key_abuseipdb}
        try:
            request = requests.get(url, headers=headers)
        except requests.exceptions.SSLError:
            self.error("SSLError connecting to %s", url)
            return _is_vpn_abuseipdb, isp

        # show what came back
        # request: <Response [200]>
        # encoding: UTF-8
        # headers: {'Date': 'Mon, 13 May 2019 20:05:34 GMT', 'Content-Type': 'text/html; charset=UTF-8', 'Transfer-Encoding': 'chunked', 'Connection': 'keep-alive', 'Set-Cookie': '__cfduid=d851c7777934; expires=Tue, 12-May-20 20:05:34 GMT; path=/; domain=.abuseipdb.com; HttpOnly, XSRF-TOKEN=eyJpxxxxxxTMifQ%3D%3D; expires=Mon, 13-May-2019 22:05:34 GMT; Max-Age=7200; path=/; secure, abuseipdb_session=eyJpxxxxxfQ%3D%3D; expires=Mon, 13-May-2019 22:05:34 GMT; Max-Age=7200; path=/; secure; httponly, CS7xxxxx%3D%3D; expires=Mon, 13-May-2019 22:05:34 GMT; Max-Age=7200; path=/; secure; httponly', 'X-Powered-By': 'PHP/7.1.21', 'Cache-Control': 'no-cache, private', 'X-RateLimit-Limit': '60', 'X-RateLimit-Remaining': '59', 'Expect-CT': 'max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"', 'Server': 'cloudflare', 'CF-RAY': '4d6333333333333c-IAD', 'Content-Encoding': 'gzip'}
        # content: b'{"data":{"ipAddress":"234.56.78.91"
        #   ,"isPublic":true
        #   ,"ipVersion":4
        #   ,"isWhitelisted":null
        #   ,"abuseConfidenceScore":0
        #   ,"countryCode":"US"
        #   ,"usageType":"Fixed Line ISP"
        #   ,"isp":"Google Fiber Inc."
        #   ,"domain":"googlefiber.net"
        #   ,"totalReports":0
        #   ,"lastReportedAt":null
        #   }}'
        # content: b'{"data":{"ipAddress":"234.56.78.91"
        # ,"isPublic":true
        # ,"ipVersion":4
        # ,"isWhitelisted":null
        # ,"abuseConfidenceScore":0
        # ,"countryCode":"AU"
        # ,"usageType":"Data Center\\/Web Hosting\\/Transit"
        # ,"isp":"Secure Internet LLC"
        # ,"domain":"purevpn.com"
        # ,"totalReports":0
        # ,"lastReportedAt":null
        # }}'

        # DEBUG test data
        # data = {'data': {'ipAddress': '234.56.78.91', 'isPublic': 'true', 'ipVersion': 4, 'isWhitelisted': 'null', 'abuseConfidenceScore': 0, 'countryCode': 'AU', 'usageType': 'Data Center\\/Web Hosting\\/Transit', 'isp': 'Secure Internet LLC', 'domain': 'purevpn.com', 'totalReports': 0, 'lastReportedAt': 'null'}}
        # _data = json.dumps(_data)
        # print(_data)

        # print(request)
        # print(request.encoding)
        # print(request.headers)
        # print(request.content)

        # parse the data
        try:
            data = request.json()
        except ValueError:
            self.warn("got non-json response from %s", url)
            return _is_vpn_abuseipdb, isp

        # print(data)

        # sort_keys: True for "pretty display"
        # print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

        # print(data["data"]["ipAddress"])
        # print(data["data"]["abuseConfidenceScore"])

        try:
            if int(data["data"]["abuseConfidenceScore"]) > _score_needed_abuseipdb:
                _is_vpn_abuseipdb = True
        except KeyError:
            self.warn("key not found: data/abuseConfidenceScore")

        try:
            domain = data["data"]["domain"]
        except KeyError:
            self.warn("key not found: data/domain")

        try:
            isp = data["data"]["isp"]
        except KeyError:
            self.warn("key not found: data/isp")

        try:
            countryCode = data["data"]["countryCode"]
        except KeyError:
            self.warn("key not found: data/countryCode")

        return _is_vpn_abuseipdb, domain, isp, countryCode

    def CheckGetIPIntel(self, _userip, _email_address_getipintel, _score_needed_getipintel=0.94):
        _is_vpn_getipintel = False

        # API documentation URL: https://getipintel.net/free-proxy-vpn-tor-detection-api/

        ## http://check.getipintel.net/check.php?ip=IPHere&contact=YourEmailAddressHere

        # make the request
        url = "http://check.getipintel.net/check.php?ip=" + _userip + "&contact=" + _email_address_getipintel
        try:
            request = requests.get(url)
        except requests.exceptions.SSLError:
            self.error("SSLError connecting to %s", url)

        # DEBUG: show what came back
        # request: < Response[200] >
        # encoding: UTF-8
        # headers: {'Date': 'Mon, 13 May 2019 21:35:46 GMT', 'Content-Type': 'text/html', 'Transfer-Encoding': 'chunked', 'Connection': 'keep-alive', 'Set-Cookie': '__cfduid=ddd0daaa46; expires=Tue, 12-May-20 21:35:46 GMT; path=/; domain=.getipintel.net; HttpOnly', 'X-Powered-By': 'PHP/5.4.45-0+deb7u14', 'Server': 'cloudflare', 'CF-RAY': '4d67cccce-IAD', 'Content-Encoding': 'gzip'}
        # content: b'{value}'
        # print(request)
        # print(request.encoding)
        # print(request.headers)
        # print(request.content)

        # DEBUG test data
        # _data = {}
        # data = json.dumps(_data)
        # print(data)

        # parse the data
        # try:
        # 	data = request.json()
        # except ValueError:
        # 	self.error("got non-json response from %s", url)
        # 	return _is_vpn_getipintel

        # print(data)
        # getipintel only returns a score value 0.0 - 1.0
        data = float(request.content)

        # sort_keys: True for "pretty display"
        # print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

        # print(_data["block"])

        if data > _score_needed_getipintel:
            _is_vpn_getipintel = True

        return _is_vpn_getipintel

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_vpncheck(self, data=None, client=None, cmd=None):
        if not data:
            client.message('^7invalid data, try !help vpncheck')
            return

        sclient = self._adminPlugin.findClientPrompt(data, client)

        if not sclient:
            # a player matching the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            cmd.sayLoudOrPM("client not found")
            return

        # -- IPHub

        cmd.sayLoudOrPM(client, 'vpncheck %s (%s)' % (sclient.cid, sclient.ip))

        _is_vpn_iphub = False
        _isp_iphub = ""
        _countryCode_iphub = ""
        if self._key_iphub and self._key_iphub != "blank":
            _is_vpn_iphub, _isp_iphub, _countryCode_iphub = self.CheckIPHub(sclient.ip, self._key_iphub)

        cmd.sayLoudOrPM(client, self.getMessage('iphub_block', str(_is_vpn_iphub)))
        cmd.sayLoudOrPM(client, self.getMessage('iphub_isp', _isp_iphub))
        cmd.sayLoudOrPM(client, self.getMessage('iphub_countryCode', _countryCode_iphub))

        # -- Abuse IPDB

        # _days_abuseipdb = 30
        # _score_needed_abuseipdb = 50
        _is_vpn_abuseipdb = False
        _domain_abuseipdb = ""
        _countryCode_abuseipdb = ""
        _isp_abuseipdb = ""
        if self._key_abuseipdb and self._key_abuseipdb != "blank":
            _is_vpn_abuseipdb, _domain_abuseipdb, _isp_abuseipdb, _countryCode_abuseipdb = self.CheckAbuseIPDB(sclient.ip, self._key_abuseipdb, self._days_abuseipdb, self._score_needed_abuseipdb)
        # self.console.write("AbuseIPDB block: %s", str(_is_vpn_abuseipdb))
        # self.console.write("AbuseIPDB isp: %s", _isp_abuseipdb)

        # self.console.write(self.getMessage('abuseipdb_block' % str(_is_vpn_abuseipdb)))
        # self.console.write(self.getMessage('abuseipdb_isp' % _isp_abuseipdb))

        cmd.sayLoudOrPM(client, self.getMessage('abuseipdb_block', str(_is_vpn_abuseipdb)))
        cmd.sayLoudOrPM(client, self.getMessage('abuseipdb_domain', _domain_abuseipdb))
        cmd.sayLoudOrPM(client, self.getMessage('abuseipdb_isp', _isp_abuseipdb))
        cmd.sayLoudOrPM(client, self.getMessage('abuseipdb_countryCode', _countryCode_abuseipdb))

        # -- GetIPIntel

        _is_vpn_getipintel = False
        # _score_needed_getipintel = 0.94
        if self._email_address_getipintel and self._email_address_getipintel != "blank":
            _is_vpn_getipintel = self.CheckGetIPIntel(sclient.ip, self._email_address_getipintel, self._score_needed_getipintel)
        # self.console.write("GetIPIntel block: %s", str(_is_vpn_getipintel))

        # self.console.write(self.getMessage('getipintel_block' % str(_is_vpn_getipintel)))

        cmd.sayLoudOrPM(client, self.getMessage('getipintel_block', str(_is_vpn_getipintel)))


####################################################################################################################
#                                                                                                                  #
#    CLASSES (copied from banlist, then trimmed down)                                                              #
#                                                                                                                  #
####################################################################################################################

class Banlist(object):

    _cronTab = None

    plugin = None
    name = None
    file = None
    message = None
    url = None
    remote_lastmodified = None
    remote_etag = None

    def __init__(self, plugin, config):
        """
        Create a new Banlist
        :param plugin: the banlist plugin instance
        :param config: the banlist plugin configuration file instance
        """
        self.plugin = plugin
        self.file_content = ""  # the banlist file content
        self.cache = {}  # used to cache isBanned results. Must be cleared after banlist file change/update
        self.cache_time = 0  # holds the modifed time of the banlist file used to fill that cache

        node = config.find('name')
        if node is None or node.text is None or node.text == '':
            self.plugin.warning("name not found in config")
        else:
            self.name = node.text

        node = config.find('file')
        if node is None or node.text is None or node.text == '':
            raise BanlistException("file not found in config")
        else:
            self.file = b3.getAbsolutePath(node.text)

        node = config.find('url')
        if node is not None and node.text != '':
            self.url = node.text

        node = config.find('message')
        if node is not None and node.text != '':
            self.message = node.text

        if not os.path.isfile(self.file):
            if self.url is None:
                raise BanlistException("file '%s' not found or not a file." % self.file)
            else:
                # create file from url
                result = self.updateFromUrl()
                if result is not True:
                    raise BanlistException("failed to create '%s' from %s. (%s)" % (self.file, self.url, result))

        elif self.url is not None:
            # check if file ues older than an hour
            fileage = (time.time() - os.stat("%s" % self.file)[8])
            self.plugin.debug("%s age is %s" % (self.file, fileage))
            if fileage > 3600:
                self.plugin.debug("[%s] file is older than an hour" % self.name)
                if self.plugin._auto_update:
                    result = self.updateFromUrl()
                    if result is not True:
                        raise BanlistException("failed to create '%s' from %s. (%s)" % (self.file, self.url, result))
                else:
                    self.plugin.warning("%s [%s] file is older than an hour, consider updating" % (self.__class__.__name__, self.name))


        if self.url is not None and self.plugin._auto_update:
            rmin = random.randint(0,59)
            self.plugin.debug("[%s] will be autoupdated at %s min of every hour" % (self.name, rmin))
            self._cronTab = b3.cron.PluginCronTab(self.plugin, self.autoUpdateFromUrl, 0, rmin, '*', '*', '*', '*')
            self.plugin.console.cron + self._cronTab

        self.plugin.info("loading %s [%s], file:[%s], url:[%s], message:[%s]" % (self.__class__.__name__, self.name,
                                                                                 self.file, self.url, self.message))

    def clear_cache(self):
        self.cache = {}
        self.cache_time = self.getModifiedTime()

    def _checkFileExists(self):
        if not os.path.isfile(self.file):
            if self.url is None:
                self.plugin.error("file '%s' not found or not a file." % self.file)
                return False
            else:
                # create file from url
                self._updateFromUrlAndCheckAll()
                return False # return False as _updateFromUrlAndCheckAll will call onBanlistUpdate
        else:
            return True

    def getMessage(self, client):
        """
        Return the message with pattern $name replaced with the banlist's name.
        """
        if self.message:
            return self.message.replace('$name','%s' % client.name)\
                .replace('$ip','%s' % client.ip)\
                .replace('$guid','%s' % client.guid)\
                .replace('$pbid','%s' % client.pbid)\
                .replace('$id','@%s' % client.id)
        else:
            return ""

    def getModifiedTime(self):
        """
        return the last modified time of the banlist file
        """
        return os.stat("%s" % self.file)[8]

    def getHumanModifiedTime(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.getModifiedTime()))

    def refreshBanlistContent(self):
        if not self._checkFileExists():
            return ""

        if self.cache_time != self.getModifiedTime():
            with open(self.file) as f:
                self.plugin.verbose("updating %s content cache from %s" % (self, self.file))
                self.file_content = f.read()
            self.clear_cache()


class IpBanlist(Banlist):

    _forceRange = None

    def __init__(self, plugin, config):
        """
        Create a new IpBanlist
        :param plugin: the banlist plugin instance
        :param config: the banlist plugin configuration file instance
        """
        Banlist.__init__(self, plugin, config)
        # set specific settings
        node = config.find('force_ip_range')
        if node is not None and string.upper(node.text) in ('YES', '1', 'ON', 'TRUE'):
            self._forceRange = True
        else:
            self._forceRange = False
        self.plugin.debug("%s [%s] force IP range : %s" % (self.__class__.__name__, self.name, self._forceRange))

    def isBanned(self, client):
        """
        Check whether a client is banned
        """
        if not client.ip:
            return False

        self.refreshBanlistContent()

        if client.ip not in self.cache:
            self.cache[client.ip] = self.isIpInBanlist(client.ip)

        rv, msg = self.cache[client.ip]
        if rv:
            self.plugin.info(msg)
        else:
            self.plugin.verbose(msg)
        return rv

    def isIpInBanlist(self, ip):
        # search the exact ip
        rStrict = re.compile(r'''^(?P<entry>%s(?:[^\d\n\r].*)?)$''' % re.escape(ip), re.MULTILINE)
        m = rStrict.search(self.file_content)
        if m:
            return ip, "ip '%s' matches banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        # search the ip with .0 at the end
        rRange = re.compile(r'''^(?P<entry>%s\.0(?:[^\d\n\r].*)?)$''' % re.escape('.'.join(ip.split('.')[0:3])), re.MULTILINE)
        m = rRange.search(self.file_content)
        if m:
            return ip, "ip '%s' matches (by range) banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        # search the ip with .0.0 at the end
        rRange = re.compile(r'''^(?P<entry>%s\.0\.0(?:[^\d\n\r].*)?)$''' % re.escape('.'.join(ip.split('.')[0:2])), re.MULTILINE)
        m = rRange.search(self.file_content)
        if m:
            return ip, "ip '%s' matches (by range) banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        # search the ip with .0.0.0 at the end
        rRange = re.compile(r'''^(?P<entry>%s\.0\.0\.0(?:[^\d\n\r].*)?)$''' % re.escape('.'.join(ip.split('.')[0:1])), re.MULTILINE)
        m = rRange.search(self.file_content)
        if m:
            return ip, "ip '%s' matches (by range) banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        # if force range is set, enforce search by range even if banlist ip are not ending with ".0"
        if self._forceRange:
            rForceRange = re.compile(r'''^(?P<entry>%s\.\d{1,3}(?:[^\d\n\r].*)?)$''' % re.escape('.'.join(ip.split('.')[0:3])), re.MULTILINE)
            m = rForceRange.search(self.file_content)
            if m:
                return ip, "ip '%s' matches (by forced range) banlist entry %r (%s %s)" % (ip, m.group('entry').strip(), self.name, self.getHumanModifiedTime())

        return False, "ip '%s' not found in banlist (%s %s)" % (ip, self.name, self.getHumanModifiedTime())


class BanlistException(Exception):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)
