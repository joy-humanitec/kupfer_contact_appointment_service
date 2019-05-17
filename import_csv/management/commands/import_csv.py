import csv
import datetime
import json
import os
import string
from uuid import UUID

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from contact.models import Contact, TITLE_CHOICES

DEFAULT_FILE_NAME = 'TopKontor_Ritz.csv'
TIMEOUT_SECONDS = 30
URL_BIFROST = ''
USERNAME = ''
PASSWORD = ''
CLIENT_ID = ''


PRODUCT_FIELD_MAPPINGS = [
    # product1
    {
        "fields": {
            "name": 'AB',
            "make": 'AE',
            "part_number": 'AF',
            "reference_id": 'AG',
            "installation_date": 'AH',
            "notes": 'AI'
        }
    },
    # product2
    {
        "fields": {
            "name": 'AJ',
            "make": 'AM',
            "part_number": 'AN',
            "reference_id": 'AO',
            "installation_date": 'AP',
            "notes": 'AQ'
        }
    },
    # product3
    {
        "fields": {
            "name": 'AR',
            "part_number": 'AV',
            "make": 'AU',
            "reference_id": 'AW',
            "installation_date": 'AX',
            "notes": 'AY'
        }
    },
    # product4
    {
        "fields": {
            "name": 'AZ',
            "part_number": 'BD',
            "make": 'BC',
            "reference_id": 'BE',
            "installation_date": 'BF',
            "notes": 'BG'
        }
    },
    # product5
    {
        "fields": {
            "name": 'BH',
            "part_number": 'BL',
            "make": 'BK',
            "reference_id": 'BM',
            "installation_date": 'BN',
            "notes": 'BO'
        }
    },
    # product6
    {
        "fields": {
            "name": 'BP',
            "part_number": 'BT',
            "make": 'BS',
            "reference_id": 'BU',
            "installation_date": 'BV',
            "notes": 'BW'
        }
    },
]
# TODO: import contacts and SiteProfiles also by mappings


def _get_title_from_display(title_display):
    german_title_choices = TITLE_CHOICES + (
        ('mr', 'herr'),
        ('mrs', 'frau'),
        ('family', 'familie'),
        ('family', 'eheleute'),
    )
    title_display = title_display.lower()
    title_displays = [y[1] for y in german_title_choices]
    if title_display in title_displays:
        title_index = title_displays.index(title_display)
        return german_title_choices[title_index][0]
    return None


def _get_date_from_value(value):
    """Check for date in value."""
    if any(char.isdigit() for char in value) and len(value) == 4:
        value = f"01.01.{value}"
    date_format = '%d.%m.%Y'
    try:
        value = datetime.datetime.strptime(value, date_format)
    except ValueError:
        return None
    return str(value)


def _combine_field_cols_by_type(_type, field_name, *row_fields):
    field_value = []
    for row in row_fields:
        if row:
            field_value.append({'type': _type, field_name: row})
    return field_value


def _get_authorization_headers():
    login_url = URL_BIFROST + '/oauth/token/'
    params = {
        'client_id': CLIENT_ID,
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
    }
    response = requests.post(login_url, params, timeout=TIMEOUT_SECONDS)
    if response.status_code != 200:
        raise PermissionError(response.content)
    headers = {
        'Authorization': 'JWT ' + json.loads(response.content)['access_token_jwt'],
        'Content-Type': 'application/json'
    }
    return headers


def is_valid_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """
    try:
        UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True


class Command(BaseCommand):
    help = """
    Import CSV from a file.
    """

    row_map = dict()
    headers = {}
    cache_profile_type_ids = {}
    row = []
    counter = 0
    contact_uuid = None

    organization_uuid = None
    workflowlevel1_uuid = None
    workflowlevel1_id = None

    def add_arguments(self, parser):
        """Add --file argument to Command."""
        parser.add_argument(
            '--file', default=None, nargs='?', help='Path of file to import.',
        )

    def __init__(self):
        """
        Set general variables.
        """
        super().__init__()
        self.build_row_mapping()

        self.headers = _get_authorization_headers()
        self.set_organization()
        self.set_workflowlevel1()

    def set_organization(self):
        """Set organization_uuid."""
        url_get_organization_uuid = URL_BIFROST + 'coreuser/'
        response = requests.get(url_get_organization_uuid,
                                params={'username': USERNAME},
                                headers=self.headers,
                                timeout=TIMEOUT_SECONDS)
        content = json.loads(response.content)[0]
        self.organization_uuid = content['organization']['organization_uuid']
        print(f"ORGANIZATION_UUID: {self.organization_uuid}")

    def set_workflowlevel1(self):
        """Set workflowlevel1_id and workflowlevel1_uuid."""
        url_get_organization_uuid = URL_BIFROST + 'workflowlevel1/'
        response = requests.get(url_get_organization_uuid,
                                headers=self.headers,
                                timeout=TIMEOUT_SECONDS)
        content = json.loads(response.content)[0]
        self.workflowlevel1_id = content['id']
        self.workflowlevel1_uuid = content['level1_uuid']
        print(f"WORKFLOWLEVEL1_ID: {self.workflowlevel1_id}")
        print(f"WORKFLOWLEVEL1_UUID: {self.workflowlevel1_uuid}")

    def build_row_mapping(self):
        """Build row mapping for easier access to rows by letter-index instead of number-index."""
        count = 0
        for l in string.ascii_uppercase:
            self.row_map.update({l: count})
            count += 1
        for i in string.ascii_uppercase:
            for j in string.ascii_uppercase:
                self.row_map.update({i + j: count})
                count += 1

    def _col(self, letter_index):
        return self.row[self.row_map[letter_index]]

    def _create_workflowlevel2(self):
        url_create_wfl2 = URL_BIFROST + 'workflowlevel2/'
        response = requests.post(url_create_wfl2,
                                 headers=self.headers,
                                 data=json.dumps({'name': 'FROM DATA IMPORT',
                                                  'workflowlevel1': self.workflowlevel1_id}))
        return json.loads(response.content)['level2_uuid']

    def _get_or_create_profile_type(self, profile_type):
        """Get or create profile_type in location_service."""
        profile_type_id = None
        if profile_type in self.cache_profile_type_ids:  # first check cache
            profile_type_id = self.cache_profile_type_ids[profile_type]
        else:
            url_get_profile_types = URL_BIFROST + 'location/profiletypes'
            response = requests.get(url_get_profile_types,
                                    headers=self.headers,
                                    timeout=TIMEOUT_SECONDS)
            results = json.loads(response.content)['results']
            # check if profile_type already in GET but not yet cached
            for pt in results:
                if pt['name'] == profile_type:
                    profile_type_id = pt['id']
                    break
            if not profile_type_id:
                url_create_profile_type = url_get_profile_types
                response = requests.post(url_create_profile_type,
                                         headers=self.headers,
                                         data=json.dumps({"name": profile_type}),
                                         timeout=TIMEOUT_SECONDS)
                profile_type_id = json.loads(response.content)['id']
            # add to cache
            self.cache_profile_type_ids[profile_type] = profile_type_id
        return profile_type_id

    def _save_site_profile(self, profile_type, address_data, wfl2_uuid, site_profile_uuid=None):
        """Create or update site profile with profile_type_id."""
        profile_type_id = self._get_or_create_profile_type(profile_type)
        site_profile_data = json.dumps({
            'workflowlevel2_uuid': wfl2_uuid,
            'profiletype': profile_type_id,
            'country': 'DE',
            **address_data}
        )
        if site_profile_uuid:
            # update
            url_update_site_profile = URL_BIFROST + f'location/siteprofiles/{site_profile_uuid}/'
            response = requests.put(url_update_site_profile, headers=self.headers,
                                    data=site_profile_data, timeout=TIMEOUT_SECONDS)
            if response.status_code != 200:
                print(f'Error when updating SiteProfile: {site_profile_uuid} - status_code: {response.status_code}')
            print(f'SiteProfile for object_with_billing {site_profile_uuid} updated.')
        else:
            url_create_site_profile = URL_BIFROST + f'location/siteprofiles/'
            response = requests.post(url_create_site_profile, headers=self.headers, data=site_profile_data)
            site_profile_uuid = json.loads(response.content)['uuid']
            print(f'SiteProfile for object_with_billing {site_profile_uuid} created.')
        return site_profile_uuid

    def _import_contact(self):
        # get or create contact by uuid
        self.contact_uuid = self._col('B')
        contact, created = Contact.objects.get_or_create(
            uuid=self.contact_uuid,
            defaults={'organization_uuid': self.organization_uuid,
                      'workflowlevel1_uuids': [self.workflowlevel1_uuid, ]}
        )

        # get attributes
        contact.customer_id = self._col('A')
        # full_name = self._col('E')
        contact.first_name = self._col('C')
        contact.last_name = self._col('D')
        contact.suffix = self._col('E')
        contact.title = _get_title_from_display(self._col('F'))
        contact.company = self._col('G')

        # phones
        home_phones = _combine_field_cols_by_type('home', 'number', self._col('H'))
        fax_phones = _combine_field_cols_by_type('fax', 'number', self._col('I'))
        mobile_phones = _combine_field_cols_by_type('mobile', 'number', self._col('J'))
        # office_phones = _combine_field_cols_by_type('office', 'number', self._col('BE'))
        contact.phones = home_phones + fax_phones + mobile_phones  # + office_phones

        # emails
        office_emails = _combine_field_cols_by_type('office', 'email', self._col('K'))
        contact.emails = office_emails

        contact.notes = self._col('L')

        # workflowlevel2_uuid
        if not contact.workflowlevel2_uuids:
            contact.workflowlevel2_uuids = [self._create_workflowlevel2(), ]

        contact.save()

        if created:
            print(f"{self.counter}: Contact with uuid={self.contact_uuid} created.")
        else:
            print(f"{self.counter}: Contact with uuid={self.contact_uuid} updated.")

        return contact.siteprofile_uuids, contact.workflowlevel2_uuids[0]

    def _import_siteprofile(self, site_profile_uuids, wfl2_uuid):
        """

        :param site_profile_uuids: For checking if the siteprofiles were already imported.
        :param wfl2_uuid: For the relation to the products.
        :return: The site_profile_uuid for setting it on the contact in case it was newly created.

        All imported siteprofiles are "object_with_billing".

        name -> street & house number, postal code, city
        address_line1 -> street & house number
        postcode -> postal code
        city -> City

        """
        object_with_billing_address_data = {
            'name': f"{self._col('M')}, {self._col('O')} {self._col('P')}",
            'address_line1': self._col('M'),
            'postcode': self._col('O'),
            'city': self._col('P'),
            'notes': self._col('Q'),
        }
        if site_profile_uuids:
            object_with_billing_site_profile_uuid = site_profile_uuids[0]
        else:
            object_with_billing_site_profile_uuid = None

        object_with_billing_site_profile_uuid = self._save_site_profile(
            'object_with_billing', object_with_billing_address_data, wfl2_uuid, object_with_billing_site_profile_uuid)
        return [object_with_billing_site_profile_uuid, ]

    def _set_site_profile_uuid_on_contact(self, site_profile_uuids):
        """Get contact_uuid and set site_profile_uuids on contact."""
        qs = Contact.objects.filter(uuid=self.contact_uuid)
        qs.update(siteprofile_uuids=site_profile_uuids)

    def _check_product_existence(self, wfl2_uuid, product_name):
        """Check if product already exists."""
        url_get_products = URL_BIFROST + 'products/products'
        response = requests.get(url_get_products,
                                params={'workflowlevel2_uuid': wfl2_uuid},
                                headers=self.headers)
        content = json.loads(response.content)['results']
        for product in content:
            if product['name'] == product_name:
                return product['uuid']
        return None

    def _update_product(self, product_uuid, product_data):
        url_update_product = URL_BIFROST + f'products/products/{product_uuid}'
        response = requests.patch(url_update_product, headers=self.headers, data=json.dumps(product_data))
        if response.status_code == 200:
            print(f"Product with uuid={product_uuid} updated.")
        else:
            print(f"Error when updating Product with uuid={product_uuid}.")
            print(response.content)

    def _create_product(self, product_data):
        url_create_product = URL_BIFROST + 'products/products/'
        response = requests.post(url_create_product, headers=self.headers, data=json.dumps(product_data))
        if response.status_code == 201:
            print(f"Product with uuid={json.loads(response.content)['uuid']} created.")
        else:
            print(f"Error when creating Product: {product_data['name']}")
            print(response.content)

    def _import_product(self, wfl2_uuid):
        """
        Field mappings look currently like this:
        {
            "fields": {
                "name": 'AB',
                "make": 'AE',
                "part_number": 'AF',
                "reference_id": 'AG',
                "installation_date": 'AH',
                "notes": 'AI'
            }
        },
        """
        initial_product_data = {
            'workflowlevel2_uuid': wfl2_uuid,
        }
        for mapping in PRODUCT_FIELD_MAPPINGS:
            product_data = dict()
            for key, value in mapping['fields'].items():
                product_data = {**product_data, **{key: self._col(value)}}
            product_data['installation_date'] = _get_date_from_value(product_data['installation_date'])
            product_data = {**product_data, **initial_product_data}
            product_name = product_data['name']
            if not product_name:
                continue
            product_uuid = self._check_product_existence(wfl2_uuid, product_name)
            if product_uuid:
                self._update_product(product_uuid, product_data)
            else:
                self._create_product(product_data)

    def parse_file(self, csv_path):
        google_csv_delimiter = ","
        # numbers_csv_delimiter = ";"
        delimiter = google_csv_delimiter
        # ToDo: find out and set delimiter dynamically
        with open(csv_path, 'rt') as csv_file:
            next(csv_file)  # skip first line
            for row in csv.reader(csv_file, delimiter=delimiter, dialect=csv.excel_tab):
                self.row = row
                if not is_valid_uuid(self._col('B')):
                    print(f"{self._col('B')} DISMISSED")
                    continue
                self.counter += 1
                site_profile_uuids, wfl2_uuid = self._import_contact()
                site_profile_uuids = self._import_siteprofile(site_profile_uuids, wfl2_uuid)
                self._set_site_profile_uuid_on_contact(site_profile_uuids)
                # TODO: SiteProfiles #2 and #3
                # site_profile_uuids = self._import_siteprofile(mappings, site_profile_uuids, wfl2_uuid)
                # self._set_site_profile_uuid_on_contact(site_profile_uuids)
                self._import_product(wfl2_uuid)
        print(f"{self.counter} contacts parsed.")

    def handle(self, *args, **options):
        file = options.get('file')
        if not file:
            file = DEFAULT_FILE_NAME
        csv_path = os.path.join(settings.BASE_DIR, '..', 'data', 'crm_service', file)
        print(f"Import data from {file}.")
        self.parse_file(csv_path)
