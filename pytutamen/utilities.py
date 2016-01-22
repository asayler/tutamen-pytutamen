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
from . import storage


### Constants ###

_DEFAULT_CN = 'new_client_cert'
_DEFAULT_COUNTRY = 'US'
_DEFAULT_STATE = 'Colorado'
_DEFAULT_LOCALITY = 'Boulder'
_DEFAULT_ORGANIZATION = 'libtutamen_client'
_DEFAULT_OU = 'libtutamen_client_crt'

### Functions ###

def setup_new_ac_server(name, url, conf=None, conf_path=None):

    # Setup Conf
    if not conf:
        conf = config.ClientConfig(conf_path=conf_path)

    # Save Server Config
    if conf.ac_server_configured(name):
        old_url = conf.ac_server_get_url(name)
        if url != old_url:
            msg = "AC Server '{}' already configured with different URL".format(name)
            raise Exception(msg)
    else:
        conf.ac_server_set_url(name, url)

    # Update Defaults
    if not conf.defaults_get_ac_server():
        conf.defaults_set_ac_server(name)

def setup_new_storage_server(name, url, conf=None, conf_path=None):

    # Setup Conf
    if not conf:
        conf = config.ClientConfig(conf_path=conf_path)

    # Save Server Config
    if conf.storage_server_configured(name):
        old_url = conf.storage_server_get_url(name)
        if url != old_url:
            msg = "Storage Server '{}' already configured with different URL".format(name)
            raise Exception(msg)
    else:
        conf.storage_server_set_url(name, url)

    # Update Defaults
    if not conf.defaults_get_storage_server():
        conf.defaults_set_storage_server(name)

def setup_new_account(ac_server_name=None, cn=None,
                      country=None, state=None, locality=None,
                      organization=None, ou=None,
                      email=None,
                      account_userdata=None, account_uid=None,
                      client_userdata=None, client_uid=None,
                      conf=None, conf_path=None):

    # Normalize Args
    if not cn:
        cn = _DEFAULT_CN
    if not country:
        country = _DEFAULT_COUNTRY
    if not state:
        state = _DEFAULT_STATE
    if not locality:
        locality = _DEFAULT_LOCALITY
    if not organization:
        organization = _DEFAULT_ORGANIZATION
    if not ou:
        ou = _DEFAULT_OU

    # Setup Conf
    if not conf:
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

def setup_collection(col_uid=None,
                     verifiers=None, verifier_uid=None,
                     accounts=None, authenticators=None,
                     conf=None, conf_path=None,
                     ac_server_names=None, storage_server_names=None,
                     account_uid=None, client_uid=None):

    ## Arg Defaults ##
    if not conf:
        conf = config.ClientConfig(conf_path=conf_path)
    if not ac_server_names:
        ac_server_names = [None]
    if not storage_server_names:
        storage_server_names = [None]
    if not account_uid:
        account_uid = conf.defaults_get_account_uid()
        if not account_uid:
            raise(ValueError("Missing Default Account UID"))

    ## Setup Server Connections ##
    acs = []
    for name in ac_server_names:
        ac = accesscontrol.ACServerConnection(ac_server_name=name,
                                              conf=conf, conf_path=conf_path,
                                              account_uid=account_uid, client_uid=client_uid)
        ac.open()
        acs.append(ac)

    sss = []
    for name in storage_server_names:
        ss = storage.StorageServerConnection(storage_server_name=name,
                                             conf=conf, conf_path=conf_path)
        ss.open()
        sss.append(ss)

    ## Setup API Clients ##
    ath_clients = []
    verifier_clients = []
    permission_clients = []
    for ac in acs:
        ath_clients.append(accesscontrol.AuthorizationsClient(ac))
        verifier_clients.append(accesscontrol.VerifiersClient(ac))
        permission_clients.append(accesscontrol.PermissionsClient(ac))

    col_clients = []
    for ss in sss:
        col_clients.append(storage.CollectionsClient(ss))

    ## Setup Verifier ##
    if not verifiers:

        if not verifier_uid:
            verifier_uid = uuid.uuid4()
        if not accounts:
            accounts = [account_uid]
        if not authenticators:
            authenticators = []

        for client in verifier_clients:
            uid = client.create(uid=verifier_uid, accounts=accounts,
                                authenticators=authenticators)
            assert(uid == verifier_uid)

        verifiers = [verifier_uid]

    ## Setup Collection ##
    if not col_uid:
        col_uid = uuid.uuid4()

    # Setup Collection Perms
    for client in permission_clients:
        client.create("collection", objuid=col_uid, v_default=verifiers)

    # Get Server Collection Create Authorizations
    objtype = storage.TYPE_SRV
    objuid = None
    objperm = storage.PERM_SRV_COL_CREATE
    tokens = []
    for client in ath_clients:
        authz_uid = client.request(objtype, objuid, objperm)
        authz_tok = client.wait_token(authz_uid)
        if authz_tok:
            tokens.append(authz_tok)
    if not tokens:
        raise Exception("No valid collection creation tokens")

    # Create Collections
    ac_servers = []
    for ac in acs:
        ac_servers.append(ac.url_srv)
    for client in col_clients:
        uid = client.create(tokens, ac_servers, uid=col_uid)
        assert(uid == col_uid)

    ## Close Connections ##
    for ac in acs:
        ac.close()
    for ss in sss:
        ss.close()

    ## Return ##
    return col_uid, verifiers

def store_secret(sec_data, sec_uid=None, col_uid=None,
                 verifiers=None, verifier_uid=None,
                 accounts=None, authenticators=None,
                 conf=None, conf_path=None,
                 ac_server_names=None, storage_server_names=None,
                 account_uid=None, client_uid=None):

    ## Arg Defaults ##
    if not ac_server_names:
        ac_server_names = [None]
    if not storage_server_names:
        storage_server_names = [None]

    ## Setup Collection ##
    if not col_uid:
        col_uid, verifiers = setup_collection(verifiers=verifiers, verifier_uid=verifier_uid,
                                              accounts=accounts, authenticators=authenticators,
                                              conf=conf, conf_path=conf_path,
                                              ac_server_names=ac_server_names,
                                              storage_server_names=storage_server_names,
                                              account_uid=account_uid, client_uid=client_uid)

    ## Setup Server Connections ##
    acs = []
    for name in ac_server_names:
        ac = accesscontrol.ACServerConnection(ac_server_name=name,
                                              conf=conf, conf_path=conf_path,
                                              account_uid=account_uid, client_uid=client_uid)
        ac.open()
        acs.append(ac)

    sss = []
    for name in storage_server_names:
        ss = storage.StorageServerConnection(storage_server_name=name,
                                             conf=conf, conf_path=conf_path)
        ss.open()
        sss.append(ss)

    ## Setup API Clients ##
    ath_clients = []
    for ac in acs:
        ath_clients.append(accesscontrol.AuthorizationsClient(ac))

    sec_clients = []
    for ss in sss:
        sec_clients.append(storage.SecretsClient(ss))

    ## Setup Secret ##

    if not sec_uid:
        sec_uid = uuid.uuid4()

    # Get Collection Create Authorizations
    objtype = storage.TYPE_COL
    objuid = col_uid
    objperm = storage.PERM_COL_CREATE
    tokens = []
    for ath_client in ath_clients:
        authz_uid = ath_client.request(objtype, objuid, objperm)
        authz_tok = ath_client.wait_token(authz_uid)
        if authz_tok:
            tokens.append(authz_tok)
    if not tokens:
            raise Exception("No valid secret creation tokens")

    # Create Secret
    # Todo: shard
    for sec_client in sec_clients:
        uid = sec_client.create(tokens, col_uid, sec_data, uid=sec_uid)
        assert(uid == sec_uid)

    ## Close Connections ##
    for ac in acs:
        ac.close()
    for ss in sss:
        ss.close()

    ## Return ##
    return sec_uid, col_uid, verifiers

def fetch_secret(sec_uid, col_uid,
                 conf=None, conf_path=None,
                 ac_server_names=None, storage_server_names=None,
                 account_uid=None, client_uid=None):

    ## Arg Defaults ##
    if not ac_server_names:
        ac_server_names = [None]
    if not storage_server_names:
        storage_server_names = [None]

    ## Setup Server Connections ##
    acs = []
    for name in ac_server_names:
        ac = accesscontrol.ACServerConnection(ac_server_name=name,
                                              conf=conf, conf_path=conf_path,
                                              account_uid=account_uid, client_uid=client_uid)
        ac.open()
        acs.append(ac)

    sss = []
    for name in storage_server_names:
        ss = storage.StorageServerConnection(storage_server_name=name,
                                             conf=conf, conf_path=conf_path)
        ss.open()
        sss.append(ss)

    ## Setup API Clients ##
    ath_clients = []
    for ac in acs:
        ath_clients.append(accesscontrol.AuthorizationsClient(ac))

    sec_clients = []
    for ss in sss:
        sec_clients.append(storage.SecretsClient(ss))

    ## Fetch Secret ##

    # Get Collection Create Authorizations
    objtype = storage.TYPE_COL
    objuid = col_uid
    objperm = storage.PERM_COL_READ
    tokens = []
    for ath_client in ath_clients:
        authz_uid = ath_client.request(objtype, objuid, objperm)
        authz_tok = ath_client.wait_token(authz_uid)
        if authz_tok:
            tokens.append(authz_tok)
    if not tokens:
            raise Exception("No valid secret creation tokens")

    # Create Secret
    # Todo: unshard
    for sec_client in sec_clients:
        sec = sec_client.fetch(tokens, col_uid, sec_uid)
        sec_data = sec['data']

    ## Close Connections ##
    for ac in acs:
        ac.close()
    for ss in sss:
        ss.close()

    ## Return ##
    return sec_data
