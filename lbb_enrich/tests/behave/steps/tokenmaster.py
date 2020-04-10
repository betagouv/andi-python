from behave import given, when, then
from lbb_enrich.lib import TokenMaster
import os
import copy
import datetime


@given(u'the tokenmaster')
def step_impl(context):
    context.tokenmaster = TokenMaster(
        client_id=os.getenv('PE_CLIENT_ID'),
        secret=os.getenv('PE_SECRET')
    )


@when(u'I query a token')
def step_impl(context):
    context.newtoken = False
    context.newtoken = context.tokenmaster.get()
    print(context.newtoken)


@when(u'I force a new token')
def step_impl(context):
    context.newtoken = False
    context.newtoken = context.tokenmaster.get(True)
    print(context.newtoken)


@then(u'I get a token')
def step_impl(context):
    assert context.newtoken


@then(u'I store that token')
def step_impl(context):
    context.oldtoken = False
    context.oldtoken = copy.copy(context.newtoken)


@then(u'it is the same one as before')
def step_impl(context):
    assert context.oldtoken == context.newtoken


@when(u'I invalidate that token in the tokenmaster')
def step_impl(context):
    context.tokenmaster._token = 'poulet_sauce_morilles'


@then(u'it is a new one')
def step_impl(context):
    print('new', context.newtoken)
    print('old', context.oldtoken)
    assert context.oldtoken != context.newtoken


@when(u'I expire that token in the tokenmaster')
def step_impl(context):
    context.tokenmaster._eol = datetime.datetime.now() - datetime.timedelta(1, 60)


@then(u'it is valid')
def step_impl(context):
    assert context.tokenmaster.is_valid(context.newtoken)


@then(u'it is invalid')
def step_impl(context):
    assert context.tokenmaster.is_valid(context.newtoken) is False
