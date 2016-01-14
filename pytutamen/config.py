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

import configparser
import uuid
import os.path


### Constants ###

_DEFAULT_CONFIG_PATH = "~/.config/pytutamen_client"

_SUB_AC = "srv_ac"
_SUB_SS = "srv_ss"
_SUB_ACCOUNTS = "accounts"
_SUB_CLIENTS = "clients"

_FILE_CORE = "core.conf"
_FILE_SRV = "servers.conf"
_FILE_KEY = "key.pem"
_FILE_CSR = "csr.pem"
_FILE_CRT = "crt.pem"

_SEC_DEFAULTS = "defaults"

_KEY_URL = "url"
_KEY_ACCOUNT = "account"
_KEY_CLIENT = "client"
_KEY_ACSRV = "ac_server"

_EXT_CONF = "conf"

### Exceptions ###


### Config Objects ###

class ClientConfig(object):

    ## Internals ##

    def __init__(self, conf_path=None):

        if not conf_path:
            conf_path = _DEFAULT_CONFIG_PATH

        conf_path = os.path.expanduser(conf_path)
        conf_path = os.path.normpath(conf_path)
        os.makedirs(conf_path, exist_ok=True)

        self._path = conf_path

    def _conf_set_section(self, conf_path, section, conf):

        conf_obj = configparser.ConfigParser()
        if os.path.isfile(conf_path):
            conf_obj.read(conf_path)

        conf_obj[section] = conf

        conf_dir = os.path.dirname(conf_path)
        os.makedirs(conf_dir, exist_ok=True)
        with open(conf_path, 'w') as conf_file:
            conf_obj.write(conf_file)

    def _conf_get_section(self, conf_path, section):

        conf_obj = configparser.ConfigParser()
        if os.path.isfile(conf_path):
            conf_obj.read(conf_path)

        if section not in conf_obj:
            return {}

        conf = conf_obj[section]

        return conf

    def _write_file(self, file_path, data):

        file_dir = os.path.dirname(file_path)
        os.makedirs(file_dir, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(data)

    def _read_file(self, file_path):

        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                data = f.read()
            return data
        else:
            return None

    ## Paths ##

    @property
    def path(self):
        return self._path

    @property
    def path_core_conf(self):
        return os.path.join(self._path, _FILE_CORE)

    @property
    def path_srv_ac(self):
        return os.path.join(self.path, _SUB_AC)

    @property
    def path_srv_ac_conf(self):
        return "{}.{}".format(self.path_srv_ac, _EXT_CONF)

    @property
    def path_srv_ss(self):
        return os.path.join(self.path, _SUB_SS)

    @property
    def path_accounts(self):
        return os.path.join(self.path, _SUB_ACCOUNTS)

    def path_account(self, account_uid):
        return os.path.join(self.path_accounts, str(account_uid))

    def path_clients(self, account_uid):
        return os.path.join(self.path_account(account_uid), _SUB_CLIENTS)

    def path_client(self, account_uid, client_uid):
        return os.path.join(self.path_clients(account_uid), str(client_uid))

    ## DEFAULTS ##

    def defaults_get_ac_server(self):

        conf = self._conf_get_section(self.path_core_conf, _SEC_DEFAULTS)
        return conf.get(_KEY_ACSRV, None)

    def defaults_set_ac_server(self, name):

        conf = self._conf_get_section(self.path_core_conf, _SEC_DEFAULTS)
        conf[_KEY_ACSRV] = name
        self._conf_set_section(self.path_core_conf, _SEC_DEFAULTS, conf)

    def defaults_get_account_uid(self):

        conf = self._conf_get_section(self.path_core_conf, _SEC_DEFAULTS)
        uid = conf.get(_KEY_ACCOUNT, None)
        return uuid.UUID(uid) if uid else None

    def defaults_set_account_uid(self, uid):

        conf = self._conf_get_section(self.path_core_conf, _SEC_DEFAULTS)
        conf[_KEY_ACCOUNT] = str(uid)
        self._conf_set_section(self.path_core_conf, _SEC_DEFAULTS, conf)

    def defaults_get_client_uid(self):

        conf = self._conf_get_section(self.path_core_conf, _SEC_DEFAULTS)
        uid = conf.get(_KEY_CLIENT, None)
        return uuid.UUID(uid) if uid else None

    def defaults_set_client_uid(self, uid):

        conf = self._conf_get_section(self.path_core_conf, _SEC_DEFAULTS)
        conf[_KEY_CLIENT] = str(uid)
        self._conf_set_section(self.path_core_conf, _SEC_DEFAULTS, conf)

    ## AC Server ##

    def ac_server_configured(self, srv):

        conf = self._conf_get_section(self.path_srv_ac_conf, srv)
        return bool(conf)

    def ac_server_set_url(self, name, url):

        conf = self._conf_get_section(self.path_srv_ac_conf, name)
        conf[_KEY_URL] = url
        self._conf_set_section(self.path_srv_ac_conf, name, conf)

    def ac_server_get_url(self, name):

        conf = self._conf_get_section(self.path_srv_ac_conf, name)
        return conf.get(_KEY_URL, None)

    ## CLIENT ##

    def client_set_key(self, account_uid, client_uid, key_pem):

        client_path = self.path_client(account_uid, client_uid)
        key_path = os.path.join(client_path, _FILE_KEY)
        self._write_file(key_path, key_pem)

    def client_get_key(self, account_uid, client_uid):

        client_path = self.path_client(account_uid, client_uid)
        key_path = os.path.join(client_path, _FILE_KEY)
        return self._read_file(key_path, key_pem)

    def client_set_csr(self, account_uid, client_uid, csr_pem):

        client_path = self.path_client(account_uid, client_uid)
        csr_path = os.path.join(client_path, _FILE_CSR)
        self._write_file(csr_path, csr_pem)

    def client_get_csr(self, account_uid, client_uid):

        client_path = self.path_client(account_uid, client_uid)
        csr_path = os.path.join(client_path, _FILE_CSR)
        return self._read_file(csr_path, csr_pem)

    def client_set_crt(self, account_uid, client_uid, srv, crt_pem):

        client_path = self.path_client(account_uid, client_uid)
        crt_path = os.path.join(client_path, _FILE_CRT)
        self._write_file(crt_path, crt_pem)

    def client_get_crt(self, account_uid, client_uid, srv):

        client_path = self.path_client(account_uid, client_uid)
        crt_path = os.path.join(client_path, "{}_{}".format(srv, _FILE_CRT))
        return self._read_file(crt_path, crt_pem)
