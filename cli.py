#!/usr/bin/env python3


### Imports ###

import sys
import json
import os
import uuid

import requests
import click


### Constants ###

_APP_NAME = 'tutamen-cli'
_PATH_SERVER_CONF = os.path.join(click.get_app_dir(_APP_NAME), 'servers')


### CLI Root ###

@click.group()
@click.option('--url', prompt=True, help="API URL")
@click.option('--cert', prompt=True, help="API Certificate File",
              type=click.Path(resolve_path=True, exists=True, readable=True, dir_okay=False))
@click.option('--key', prompt=True, help="API Private Key File",
              type=click.Path(resolve_path=True, exists=True, readable=True, dir_okay=False))
@click.pass_context
def cli(ctx, url, cert, key):
    """COG CLI"""

    # Setup Context
    ctx.obj = {}
    ctx.obj['url'] = url
    ctx.obj['path_cert'] = cert
    ctx.obj['path_key'] = key


### Secret Storage Commands ###

@cli.group(name='secret')
@click.pass_obj
def secret(obj):
    pass

@secret.command(name='get')
@click.pass_obj
def secret_get(obj):
    pass

@secret.command(name='put')
@click.pass_obj
def secret_put(obj):
    pass


### Main ###

if __name__ == '__main__':
    sys.exit(cli())
