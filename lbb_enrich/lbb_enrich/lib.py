import requests
import datetime
import json
import time
import logging
import psycopg2
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

# api_bonneboite default return page size
DEFAULT_PAGE_SIZE = 100

# liste des departements visés
DEPARTMENTS = [33, 69, 35, 17, 63, 77, 91, 78, 25, 92, 93, 94, 95]


# Flag identifying parsed rows in the database
DB_FLAG = 'boe_poleemploi'


class TokenMaster:
    """
    Token master is the master of tokens.
    He provides valid tokens to those in need.
    Should a token fail its duty, a new one can be issued.
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
            # Entering retry loop
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
        if force:
            self.logger.warning('Force querying new token')
        self._token_reset()
        time.sleep(TOKEN_OBTENTION_PAUSE_SECS)
        # THIS will crash if excessive redundancy reached, which will mean
        # more concerning things have happened which demand immediate attention
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


class ApiConnector:
    """
    This is the one querying the API.
    He needs a tokenmaster though
    what you want from him you should know.
    """
    _retries = 2

    def __init__(self, tokenMaster):
        self.tkm = tokenMaster
        self.logger = logging.getLogger(__name__)

    def _prepare_return(self, data):
        # Format return data
        return [{'siret': c['siret'], 'url': c['url'], 'boe': c['boe']} for c in data]

    def query(self, lat, lon, dist, rome_codes, naf_codes=False, page_size=DEFAULT_PAGE_SIZE):
        params = {
            'distance': dist,
            'latitude': lat,
            'longitude': lon,
            'page_size': page_size
        }
        if naf_codes:
            params['naf_codes'] = naf_codes

        while True:
            # Entering retry loop
            resp = requests.get(
                'https://api.emploi-store.fr/partenaire/labonneboite/v1/company/',
                params=params,
                headers={'Authorization': 'Bearer ' + self.tkm.get()}
            )
            try:
                resp.raise_for_status
                break
            except Exception:
                self.logger.warning('Failed to query labonneboite api: %s; retrying', resp)
                self._retries -= 1
                self.tkm.get(force=True)
                if self._retries <= 0:
                    self.logger.critical('Can\'t recover, calling it quits')
                    raise
        return self._prepare_return(resp.json())


class DbAccess:
    """
    Database accessor
    """
    _conn = False

    def __init__(self, config):
        self._conn = psycopg2.connect(**config['pg'])
        self.logger = logging.getLogger(__name__)

    def get_companies(self, limit=100):
        """
        Obtain a list of randomly select companies
        not already enriched
        and within the list of departments
        """
        sql_raw = """
        SELECT siret, lat, lon, departement, naf 
        FROM entreprises WHERE departement IN {departements}
        AND '{flag}' != ANY(flags) ORDER BY random() limit {limit};
        """

        strings = {
            'flag': DB_FLAG,
            'departements': DEPARTMENTS,
            'limit': limit
        }

        sql = sql_raw.format(**strings)
        self.logger.debug('company sql: %s', sql)
