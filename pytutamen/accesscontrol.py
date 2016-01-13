# -*- coding: utf-8 -*-


# Andy Sayler
# 2016
# pytutamen Package
# Access Control Client


### Imports ###

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

import requests

from . import api_client


### Constants ###

_EP_BOOTSTRAP = "bootstrap"
_KEY_ACCOUNTS = "accounts"
_KEY_CLIENTS = "clients"


### Exceptions ###

class APIACException(api_client.APIClientException):
    pass


### Client Objects ###

class AccountClient(api_client.ObjectClient):

    def bootstrap(self, account_userdata={}, account_uid=None,
                  client_userdata={}, client_uid=None, client_csr=None):

        if not client_csr:
            raise ValueError("client_csr required")

        ep = "{}/{}".format(_EP_BOOTSTRAP, _KEY_ACCOUNTS)

        json_out = {'account_userdata': account_userdata,
                    'client_userdata': client_userdata}
        if account_uid:
            json_out['account_uid'] = str(account_uid)
        if client_uid:
            json_out['client_uid'] = str(client_uid)

        res = self._apiclient.http_post(ep, json=json_out)
        account_uid = uuid.UUID(res[_KEY_ACCOUNTS][0])
        client_uid = uuid.UUID(res[_KEY_CLIENTS][0])
        return (account_uid, client_uid)
