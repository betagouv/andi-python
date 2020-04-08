import requests
import datetime
import json
import time
import logging
#
# Lib has to contain a function able to, from a query,
# Generate a list with sirets, urls and BOE flags
# Secondary objective: extract contact information from provided URL
#
# Effects:
# - Set BOE flag on all companies found
# - Add contact info if available
# - Tag db records whenever possible

# Pause time before asking for a new token (naïve rate limiting)
TOKEN_OBTENTION_PAUSE_SECS = 1


class TokenMaster:
    """
    Token master is the master of tokens.
    """

    _token = False
    _eol = False
    _client_id = False
    _secret = False
    # Re-connect retries
    _retries = 3

    def __init__(self, *, client_id, secret):
        self._client_id = client_id
        self._secret = secret
        self.logger = logging.getLogger(__name__)

    def _token_is_ok(self):
        now = datetime.datetime.now()
        if self._token and self._eol and now < self._eol:
            return True
        return False

    def _token_reset(self):
        accessdata = {
            'grant_type': 'client_credentials',
            'client_id': self._client_id,
            'client_secret': self._secret,
            'scope': 'application_%s %s' % (self._client_id, 'api_labonneboitev1'),
        }
        while True:
            self.logger.info('Querying token')
            auth_request = requests.post(
                'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
                data=accessdata)
            try:
                auth_request.raise_for_status()
                break
            except Exception as error:
                self._retries -= 1
                self.logger.warning('Failed to query token %s retries left', self._retries)
                time.sleep(TOKEN_OBTENTION_PAUSE_SECS)
                if self._retries <= 0:
                    self.logger.critical(accessdata)
                    raise ValueError('Autentication failed: {}'.format(error))

        response = auth_request.json()
        self._token = response.get('access_token')
        expires_in = datetime.timedelta(seconds=response.get('expires_in', 600))
        self._eol = datetime.datetime.now() + expires_in
        self.logger.info("Received token, expires in %s", expires_in)
        self.logger.info("Token end-of-life set @ %s", self._eol)

    def get(self, force=False):
        if not force and self._token_is_ok():
            return self._token
        self._token_reset()
        time.sleep(TOKEN_OBTENTION_PAUSE_SECS)
        # This will crash if excessive redundancy reached, which will mean
        # more concerning things have happened which demand attention
        return self.get()

    def is_valid(self, token=False):
        if not token:
            token = self._token

        params = {
            'distance': 1,
            'latitude': 49.119146,
            'longitude': 6.17602,
            'rome_codes': 'M1607',
        }
        resp = requests.get(
            'https://api.emploi-store.fr/partenaire/labonneboite/v1/company/',
            params=params,
            headers={'Authorization': 'Bearer ' + self._token}
        )
        try:
            resp.raise_for_status
            print(resp.json())
            return True
        except Exception:
            return False
