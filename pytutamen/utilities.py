# -*- coding: utf-8 -*-


# Andy Sayler
# 2016
# pytutamen Package
# Utility Functions


### Imports ###

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

import uuid

from . import config
from . import crypto
from . import accesscontrol

### Functions ###

def setup_new_ac_server(name, url, conf_path=None):

    # Setup Conf
    conf = config.ClientConfig(conf_path=conf_path)

    # Save Server Config
    if conf.ac_server_configured(name):
        old_url = conf.get_ac_server_url(name)
        if url != old_url:
            msg = "AC Server '{}' already configured with different URL".format(name)
            raise Exception(msg)
    else:
        conf.ac_server_set_url(name, url)

    # Update Defaults
    if not conf.defaults_get_ac_server():
        conf.defaults_set_ac_server(name)

def setup_new_account(ac_server_name=None, cn="new_client_cert",
                      email=None, country="US", state="Colorado", locality="Boulder",
                      organization="libtutamen_client", ou="libtutamen_client_account",
                      account_userdata=None, account_uid=None,
                      client_userdata=None, client_uid=None,
                      conf_path=None, path_ca=None):

    # Setup Conf
    conf = config.ClientConfig(conf_path=conf_path)

    # Get Server Name
    if not ac_server_name:
        ac_server_name = conf.defaults_get_ac_server()

    # Get UIDs
    if not account_uid:
        account_uid = conf.defaults_get_account_uid()
        if not account_uid:
            account_uid = uuid.uuid4()
    if not client_uid:
        client_uid = conf.defaults_get_client_uid()
        if not client_uid:
            client_uid = uuid.uuid4()

    # Check Existing CRT
    old_crt = conf.client_get_crt(account_uid, client_uid, ac_server_name)
    if old_crt:
        msg = "Client already configured for server {}".format(ac_server_name)
        raise Exception(msg)

    # Update Defaults
    if not conf.defaults_get_account_uid():
        conf.defaults_set_account_uid(account_uid)
    if not conf.defaults_get_client_uid():
        conf.defaults_set_client_uid(client_uid)

    # Generate and Save Key (if necessary)
    key_pem = conf.client_get_key(account_uid, client_uid)
    if not key_pem:
        key_pem = crypto.gen_key()
        conf.client_set_key(account_uid, client_uid, key_pem)

    # Generate and Save CSR
    csr_pem = crypto.gen_csr(key_pem, cn, country, state, locality, organization, ou, email)
    conf.client_set_csr(account_uid, client_uid, ac_server_name, csr_pem)

    # Bootstrap Account and Save CRT
    ac_connection = accesscontrol.ACServerConnection(ac_server_name=ac_server_name,
                                                     account_uid=account_uid,
                                                     client_uid=client_uid,
                                                     no_client_crt=True,
                                                     conf=conf)
    with ac_connection:
        bootstrap = accesscontrol.BootstrapClient(ac_connection)
        ret = bootstrap.account(account_userdata=account_userdata,
                                account_uid=account_uid,
                                client_userdata=client_userdata,
                                client_uid=client_uid,
                                client_csr=csr_pem)
    ret_account_uid, ret_client_uid, client_crt = ret
    conf.client_set_crt(account_uid, client_uid, ac_server_name, client_crt)

    # Check and Return
    assert account_uid == ret_account_uid
    assert client_uid == ret_client_uid
    return account_uid, client_uid, client_crt
