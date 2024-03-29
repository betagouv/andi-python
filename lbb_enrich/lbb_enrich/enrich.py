#!/usr/bin/env python3
import click
import os
import logging
import json
from lib import (
    TokenMaster,
    ApiConnector,
    DbConnector,
    get_rome_to_naf_table,
    get_rome_family_codes,
    get_naf_romes,
    get_contact_data,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())

CONFIG = {
    'postgresql': {
        'dsn': os.getenv('PG_DSN', 'postgres://user:pass@localhost:5432/db')
    },
    'pe': {
        'client_id': os.getenv('PE_CLIENT_ID'),
        'secret': os.getenv('PE_SECRET')
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
    ctx.obj['api_agent'] = ApiConnector(TokenMaster(**CONFIG['pe']))


@main.command()
@click.option('--company-list', is_flag=True, help='Test company list generator')
@click.option('--naf-to-rome', is_flag=True, help='Test rome obtention from naf code')
@click.option('--contact-extraction', is_flag=True, help='Test contact extraction')
@click.pass_context
def test(ctx, company_list, naf_to_rome, contact_extraction):
    """
    Due to time constraints, some testing has been done
    in the terminal, using this command
    """

    db = DbConnector(CONFIG['postgresql'])

    if company_list:
        print('Testing company list generator, outputting 10 companies')
        results = db.get_companies(10)
        for res in results:
            print(res)

    if naf_to_rome:
        print('Testing rome families for naf division "D"')
        print(json.dumps(get_rome_to_naf_table()['D'], indent=2))
        print('Testing rome codes for rome family "A"')
        print(json.dumps(get_rome_family_codes()['A'], indent=2))
        print('Testing rome codes for Naf code 8219Z')
        print(json.dumps(get_naf_romes('8219Z'), indent=2))

    if contact_extraction:
        # Phone number only
        url = 'https://labonneboite.pole-emploi.fr/83246875500018/details?rome_code=I1604'
        # Phone + mail + website
        # url = 'https://labonneboite.pole-emploi.fr/51345049400028/details?rome_code=N410'
        # No contact
        # url = ' https://labonneboite.pole-emploi.fr/84810244800018/details'
        response = get_contact_data(url)
        print(response)


@main.command()
@click.option('--dry-run', is_flag=True, help="Dry run (no writes)")
@click.option('--limit-run', default=20, help="Number of companies to query")
@click.option('--limit-distance', default=10, help="Max distance of search query")
@click.pass_context
def run(ctx, dry_run, limit_run, limit_distance):
    """
    Run the enricher !
    """
    db = DbConnector(CONFIG['postgresql'], dry_run=dry_run, debug=ctx.obj['debug'])
    companies = db.get_companies(limit_run)
    for company in companies:
        logger.debug('Handling company %s', company)
        romes = get_naf_romes(company['naf'])
        logger.debug('Checking romes : %s', romes)
        matches = ctx.obj['api_agent'].query(
            lat=company['lat'],
            lon=company['lon'],
            dist=limit_distance,
            rome_codes=','.join(romes),
        )
        for match in matches:
            logger.debug('Updating boe for %s, set to %s', match['siret'], match['boe'])
            db.boe_set(match['siret'], match['boe'])
            logger.debug('Trying to obtain data from %s', match['url'])
            contact_info = get_contact_data(match['url'])
            if any(contact_info.values()):
                logger.debug('Found contact information, updating')
                db.contact_set(match['siret'], contact_info)


@main.command()
@click.option('--dry-run', is_flag=True, help="Dry run (no writes)")
@click.option('--siret', default='', help="Target company siret")
@click.pass_context
def target(ctx, dry_run, siret):
    db = DbConnector(CONFIG['postgresql'], dry_run=dry_run, debug=ctx.obj['debug'])
    company = db.get_company(siret)
    print(company)
    romes = get_naf_romes(company['naf'])
    matches = ctx.obj['api_agent'].query(
        lat=company['lat'],
        lon=company['lon'],
        dist=2,
        rome_codes=','.join(romes),
    )
    needle = [m for m in matches if m['siret'] == siret]
    if len(needle) != 1:
        print("Error, found more then 1 result")
        print(needle)
    company_info = needle[0]
    print(company_info)
    contact_info = get_contact_data(company_info['url'])
    db.boe_set(company['siret'], company_info['boe'])
    db.contact_set(company['siret'], contact_info)


if __name__ == '__main__':
    main(obj={})  # pylint:disable=no-value-for-parameter, unexpected-keyword-arg
