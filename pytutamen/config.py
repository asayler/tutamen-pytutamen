# -*- coding: utf-8 -*-


# Andy Sayler
# 2016
# pytutamen Package
# Client Config


### Imports ###

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

import uuid
import os.paths


### Constants ###

_DEFAULT_CONFIG_PATH = "~/.config/pytutamen_client"

_SUB_AC = "srv_ac"
_SUB_SS = "srv_ss"
_SUB_ACCOUNTS = "accounts"
_SUB_CLIENTS = "clients"

_FILE_SRV = "servers.conf"

_KEY_URL = "url"

### Exceptions ###


### Config Objects ###



class ClientConfig(object):

    def __init__(self, conf_path=_DEFAULT_CONFIG_PATH):

        conf_path = os.path.expanduser(conf_path)
        conf_path = os.path.normpath(conf_path)
        os.makedirs(conf_path, exist_ok=True)

        self._path = conf_path

    @property
    def path(self):
        return self._path

    @property
    def path_srv_ac(self):
        return os.join(self.path, _SUB_AC)

    @property
    def path_srv_ss(self):
        return os.join(self.path, _SUB_SS)

    @property
    def path_accounts(self):
        return os.join(self.path, _SUB_ACCOUNTS)

    def path_account(self, account_uid):
        return os.join(self.path_accounts, str(account_uid))

    def path_clients(self, account_uid):
        return os.join(self.path_account(account_uid), _SUB_CLIENTS)

    def path_client(self, account_uid, client_uid):
        return os.join(self.path_clients(account_uid), str(client_uid))


    def _conf_set(self, conf_path, name, conf):

        conf_obj = configparser.ConfigParser()
        if os.path.isfile(conf_path):
            conf_obj.read(conf_path)

        if name in conf_obj:
            raise ValueError("'{}' already in configured".format(name))

        conf_obj[srv] = conf

        conf_dir = os.path.dirname(conf_path)
        os.makedirs(conf_dir, exist_ok=True)
        with open(conf_path, 'w') as conf_file:
            conf_obj.write(conf_file)

    def _conf_get(self, conf_path, name):

        conf_obj = configparser.ConfigParser()
        if os.path.isfile(conf_path):
            conf_obj.read(conf_path)

        if name not in conf_obj:
            raise ValueError("'{}' not configured".format(name))

        conf = conf_obj[name]

        return conf

    def ac_server_set_url(self, srv, url):

        conf = {}
        conf[_KEY_URL] = url

        conf_path = "{}.{}".format(self.path_srv_ac, _EXT_CONF)
        self._conf_set(conf_path, srv, conf)

    def ac_server_get_url(self, srv):

        conf_path = "{}.{}".format(self.path_srv_ac, _EXT_CONF)
        conf = self._conf_get(conf_path, srv)
        return conf[_KEY_URL]

    def client_set_key(self, srv):
        pass
