from behave import given, when, then
import os
from lbb_enrich.lib import (
    TokenMaster,
    ApiConnector,
    get_naf_romes,
    get_contact_data,
)


@given(u'a connection to the api')
def step_impl(context):
    tokenmaster = TokenMaster(
        client_id=os.getenv('PE_CLIENT_ID'),
        secret=os.getenv('PE_SECRET')
    )
    context.api = ApiConnector(tokenmaster)


@given(u'the data from a valid company')
def step_impl(context):
    context.data = {
        'siret': '50110738700034',
        'lat': 48.946158,
        'lon': 2.202827,
        'departement': '78',
        'naf': '4939A'
    }


@when(u'I query the API')
def step_impl(context):
    romes = get_naf_romes(context.data['naf'])
    context.results = context.api.query(
        lat=context.data['lat'],
        lon=context.data['lon'],
        dist=2,
        rome_codes=','.join(romes),
    )


@then(u'I have a valid response')
def step_impl(context):
    assert context.results


@then(u'the response contains the data I need')
def step_impl(context):
    context.result = [r for r in context.results if r['siret'] == context.data['siret']]
    assert len(context.result) == 1


@given(u'data from a company that does not exists')
def step_impl(context):
    context.data = {
        'siret': '50115555500034',
        'lat': 48.946158,
        'lon': 2.202827,
        'departement': '78',
        'naf': '4939A'
    }


@then(u'I receive an error')
def step_impl(context):
    pass


@given(u'a URL from a company, with contact data')
def step_impl(context):
    context.url = 'https://labonneboite.pole-emploi.fr/51345049400028/details?rome_code=N410'


@when(u'I parse the page')
def step_impl(context):
    context.data = get_contact_data(context.url)


@then(u'I get the contact information')
def step_impl(context):
    assert context.data
    assert any(context.data.values())


@given(u'a URL from a company, without contact data')
def step_impl(context):
    context.url = 'https://labonneboite.pole-emploi.fr/84810244800018/details'


@then(u'I don\'t get the contact information')
def step_impl(context):
    assert context.data
    assert not any(context.data.values())
