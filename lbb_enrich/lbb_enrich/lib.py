import requests
import datetime
import os
import yaml
import time
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from bs4 import BeautifulSoup
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
DEPARTMENTS = "('33', '69', '35', '17', '63', '77', '91', '78', '25', '92', '93', '94', '95')"

# Flag identifying parsed rows in the database
DB_FLAG = 'boe_poleemploi'
DB_CONTACT_FLAG = 'contact_poleemploi'


def get_rome_to_naf_table():
    # Deprecated
    current_dir = os.path.dirname(os.path.abspath(__file__))
    defpath = f'{current_dir}/../assets/rome_naf.yml'
    deffile = open(defpath, 'r')
    return yaml.safe_load(deffile)


def get_rome_family_codes():
    # Deprecated
    current_dir = os.path.dirname(os.path.abspath(__file__))
    defpath = f'{current_dir}/../assets/rome_list.yml'
    deffile = open(defpath, 'r')
    return yaml.safe_load(deffile)


def get_naf_romes(naf):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    defpath = f'{current_dir}/../assets/naf_div_romes.yml'
    deffile = open(defpath, 'r')
    division = naf[0:2]
    return yaml.safe_load(deffile)[division]


def get_contact_data(url):
    output = {
        'phonenumber': None,
        'email': None,
        'website': None
    }
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        target = soup.find_all('h4', text='Contact')[0].findNext('ul')
        links = target.find_all('a')
        for link in links:
            href = link['href']
            if 'tel:' in href:
                output['phonenumber'] = link.getText()
            elif 'mailto:' in href:
                output['email'] = link.getText()
            elif 'http' in href[0:5]:
                output['website'] = href
    finally:
        return output


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
        try:
            return [{'siret': c['siret'], 'url': c['url'], 'boe': c['boe']} for c in data]
        except Exception:
            self.logger.critical('Failed data preparation with data: %s', data)
            raise

    def query(self, lat, lon, dist, rome_codes, naf_codes=False, page_size=DEFAULT_PAGE_SIZE):
        params = {
            'distance': dist,
            'latitude': lat,
            'longitude': lon,
            'page_size': page_size,
            'rome_codes': rome_codes,
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
        data = resp.json()
        if 'companies' in data and data['companies']:
            return self._prepare_return(data['companies'])
        return []


class DbConnector:
    """
    Database accessor
    """
    _conn = False
    _dry_run = False

    def __init__(self, config, dry_run=False, *, debug=False):
        self._conn = psycopg2.connect(**config)
        self._conn.autocommit = True
        self.logger = logging.getLogger(__name__)
        self._dry_run = dry_run
        if debug:
            self.logger.setLevel(logging.getLevelName('DEBUG'))
            self.logger.debug('DbConnector debug enabled')
            self.logger.addHandler(logging.StreamHandler())

    def get_companies(self, limit=100):
        """
        Obtain a list of randomly select companies
        not already enriched
        and within the list of departments
        """
        sql_raw = """
        SELECT siret, lat, lon, departement, naf
        FROM entreprises
        WHERE departement IN {departements}
        AND '{flag}' <> ALL(flags)
        ORDER BY random() limit {limit};
        """

        strings = {
            'flag': DB_FLAG,
            'departements': DEPARTMENTS,
            'limit': limit
        }

        sql = sql_raw.format(**strings)
        self.logger.debug('company sql: %s', sql)

        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            results = cur.fetchall()
        return [dict(r) for r in results]

    def get_company(self, siret):
        """
        Obtain data from a single company
        """
        sql = """
        SELECT siret, lat, lon, departement, naf
        FROM entreprises
        where siret = %(siret)s;
        """

        data = {
            'siret': siret
        }

        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, data)
            results = cur.fetchall()
        return [dict(r) for r in results][0]

    def boe_set(self, siret, boe):
        """
        Set BOE flag of company
        """
        self.logger.debug('Updating company %s, set boe to %s', siret, boe)
        sql = """
        UPDATE "entreprises"
        SET
            BOE = %(boe)s,
            flags = array_append(flags, %(flag)s),
            date_updated = now()
        WHERE siret = %(siret)s
        AND %(flag)s <> ALL(flags)
        RETURNING id_internal
        """
        data = {
            'siret': siret,
            'boe': boe,
            'flag': DB_FLAG
        }

        with self._conn.cursor() as cur:
            self.logger.debug('Updating database:\nquery:%s\ndata:%s', sql, data)
            if not self._dry_run:
                cur.execute(sql, data)
                id_internal = cur.fetchone()
            else:
                id_internal = '[DRY_RUN]'
        self.logger.debug('Updated db row %s', id_internal)

    def contact_set(self, siret, contact):
        """
        Set contact info if not already defined
        """
        sql = """
        UPDATE "entreprises"
        SET
            phone_official_1 = COALESCE(%(phonenumber)s, phone_official_1),
            email_official = COALESCE(%(email)s, email_official),
            website = COALESCE(%(website)s, website),
            flags = array_append(flags, %(flag)s)
        WHERE siret = %(siret)s
        AND %(flag)s <> ALL(flags)
        RETURNING id_internal;
        """
        data = contact
        data['flag'] = DB_CONTACT_FLAG
        data['siret'] = siret
        with self._conn.cursor() as cur:
            self.logger.debug('Updating database:\nquery:%s\ndata:%s', sql, data)
            if not self._dry_run:
                cur.execute(sql, data)
                id_internal = cur.fetchone()
            else:
                id_internal = '[DRY_RUN]'
        self.logger.debug('Updated db row %s', id_internal)
