#!/usr/bin/env python3
import click
import os
import logging
from lib import (
    DbConnector
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())

CONFIG = {
    'postgresql': {
        'dsn': os.getenv('PG_DSN', 'postgres://user:pass@localhost:5432/db')
    }
}

# ################################################################### MAIN FLOW
# #############################################################################
@click.group()
@click.option('--debug', is_flag=True, default=False)
@click.pass_context
def main(ctx, debug):
    if debug:
        logger.setLevel(logging.getLevelName('DEBUG'))
        logger.debug('Debugging enabled')
        ctx.obj['debug'] = True
    else:
        ctx.obj['debug'] = False


@main.command()
@click.option('--company-list', is_flag=True, help='Test company list generator')
@click.pass_context
def test(ctx, company_list):
    db = DbConnector(CONFIG['postgresql'])
    if (company_list):
        print('Testing company list generator, outputting 10 companies')
        results = db.get_companies(10)
        for res in results:
            print(res)


if __name__ == '__main__':
    main(obj={})  # pylint:disable=no-value-for-parameter, unexpected-keyword-arg
