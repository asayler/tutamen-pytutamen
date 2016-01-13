# -*- coding: utf-8 -*-


# Andy Sayler
# 2016
# pytutamen Package
# Crypto Tools


### Imports ###

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


### Constants ###

TYPE_RSA = 'RSA'

_SUPPORTED_LENGTH = [2048, 4096]
_SUPPORTED_EXP = [3, 65537]


### Functions ###

def gen_key(length=4096, pub_exp=65537, typ=TYPE_RSA, password=None):

    if length not in _SUPPORTED_LENGTH:
        raise TypeError("Length must be one of '{}'".format(_SUPPOERTED_LENGTH))
    if pub_exp not in _SUPPORTED_EXP:
        raise TypeError("pub_exp must be one of '{}'".format(_SUPPOERTED_EXP))
    if typ != TYPE_RSA:
        raise TypeError("Only type '{}' supported".format(TYPE_RSA))

    key = rsa.generate_private_key(pub_exp, length, default_backend())

    if not password:
        encryption = serialization.NoEncryption()
    else:
        encryption = serialization.BestAvailableEncryption(password)
    key_pem = key.private_bytes(encoding=serialization.Encoding.PEM,
                                format=serialization.PrivateFormat.PKCS8,
                                encryption_algorithm=encryption).decode()

    return key_pem

def gen_csr(key_pem, cn, country, state, locality, organization, ou, email,
            password=None):

    be = default_backend()

    sub_attr = []
    sub_attr.append(x509.NameAttribute(x509.NameOID.COMMON_NAME, cn))
    sub_attr.append(x509.NameAttribute(x509.NameOID.COUNTRY_NAME, country))
    sub_attr.append(x509.NameAttribute(x509.NameOID.STATE_OR_PROVINCE_NAME, state))
    sub_attr.append(x509.NameAttribute(x509.NameOID.LOCALITY_NAME, locality))
    sub_attr.append(x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, organization))
    sub_attr.append(x509.NameAttribute(x509.NameOID.ORGANIZATIONAL_UNIT_NAME, ou))
    sub_attr.append(x509.NameAttribute(x509.NameOID.EMAIL_ADDRESS, email))

    key = serialization.load_pem_private_key(key_pem.encode(), password, be)

    builder = x509.CertificateSigningRequestBuilder()
    builder = builder.subject_name(x509.Name(sub_attr))

    csr = builder.sign(key, hashes.SHA256(), be)
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()

    return csr_pem
