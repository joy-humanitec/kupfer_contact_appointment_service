import csv
import datetime
import json
import os
import string

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
# ORGANIZATION_UUID = 'fd383104-20fa-4156-93c0-fe75d10005ab'  # Ritz GmbH on production
# workflowlevel1_uuid = '6a4c8b6e-f90b-4554-b092-9a3a77bc00de'  # WorkflowLevel1.objects.get(name='Ritz
# GmbH').level1_uuid on production  # noqa
ORGANIZATION_UUID = '460c0ed6-445b-4204-8a6e-442ebb8b97a9'  # Test Import Organization on dev
WORKFLOWLEVEL1_UUID = '7f69cdd8-11ac-421e-88a2-a2f0334109a3'  # Test Import Wfl1 on dev
WORKFLOWLEVEL1_ID = 15


def _merge_fields(*args):
    return ' '.join(filter(None, args)).strip()


def _split_full_name(full_name):
    """RULES for separating last name, first name:
    - When a user writes one word - it is assigned as the last name
    - When a user writes two words - it is assigned as first name and last name
    - When a user writes more than two words - all the words BUT the last one are assigned to the “First Name”, and
      only the last one is assigned to the “Last Name”. Except from the following:
    ---- When a user writes Last name, First name (with a comma after the first word),
         the word with comma is treated as last name
    ---- When a user writes “-” between two words - it is treated as the last name .
    """
    title = None
    full_name = full_name.strip()
    if any(char.isdigit() for char in full_name):
        first_name, last_name = '', full_name
    elif full_name.count('-') > 0:
        if ' ' in full_name:
            first_name, last_name = full_name.rsplit(' ', 1)
        else:
            first_name, last_name = '', full_name
    elif full_name.count(',') == 1:
        last_name, first_name = full_name.split(',')
    elif full_name.count(',') > 1:
        raise NotImplementedError(f'Unhandled name: {full_name}')
    elif full_name.count(' ') == 0:
        first_name, last_name = '', full_name
    elif full_name.count(' ') == 1:
        first_name, last_name = full_name.split(' ')
    elif full_name.count(' ') > 1:
        first_name, last_name = full_name.rsplit(' ', 1)
    # check if title in first_name
    title_displays = [y[1] for y in TITLE_CHOICES]
    for title_display in title_displays:
        if title_display in first_name:
            first_name = first_name.replace(title_display, '')
            title_index = title_displays.index(title_display)
            title = TITLE_CHOICES[title_index][0]
            break
    return title, first_name.strip(), last_name.strip()


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


def _combine_field_rows_by_type(_type, field_name, *row_fields):
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


class Command(BaseCommand):
    help = """
    Import CSV from a file.
    """

    row_map = dict()
    headers = {}
    cache_profile_type_ids = {}
    row = []
    counter = 0

    def __init__(self):
        """
        Build row mapping for easier access to rows by letter-index instead
        of number-index."""
        count = 0
        for l in string.ascii_uppercase:
            self.row_map.update({l: count})
            count += 1
        for i in string.ascii_uppercase:
            for j in string.ascii_uppercase:
                self.row_map.update({i + j: count})
                count += 1
        # set headers
        self.headers = _get_authorization_headers()

    def _row(self, letter_index):
        return self.row[self.row_map[letter_index]]

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', default=None, nargs='?',
            help='Path of file to import.',
        )

    def _create_workflowlevel2(self):
        url_create_wfl2 = URL_BIFROST + 'workflowlevel2/'
        response = requests.post(url_create_wfl2,
                                 headers=self.headers,
                                 data=json.dumps({'name': 'FROM DATA IMPORT',
                                                  'workflowlevel1': WORKFLOWLEVEL1_ID}))
        return json.loads(response.content)['level2_uuid']

    def _get_or_create_profile_type(self, profile_type):
        """Get or create profile_type."""
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
        else:
            url_create_site_profile = URL_BIFROST + f'location/siteprofiles/'
            response = requests.post(url_create_site_profile, headers=self.headers, data=site_profile_data)
            site_profile_uuid = json.loads(response.content)['uuid']

        return site_profile_uuid

    def _import_contact(self):
        """
        - A - UUID
        - D - Company, merge with S and F
        - E: First Name, Last name
        - K: phone number (note that it needs to be split into home and office addresses as separate phones and merged
             with other fields)
        Office phone: Merge K, BE, BF, BI,
        Home phone: Merge M, AK, CE, CF
        - L: Fax phone number, merge with CG
        - AO: email, please merge with BD
        """
        # get or create contact by uuid
        contact_uuid = self._row('A')
        contact, created = Contact.objects.get_or_create(
            uuid=contact_uuid,
            defaults={'organization_uuid': ORGANIZATION_UUID,
                      'workflowlevel1_uuids': [WORKFLOWLEVEL1_UUID, ]}
        )

        # get attributes
        company = _merge_fields(self._row('D'), self._row('S'), self._row('F'))
        full_name = self._row('E')
        title, first_name, last_name = _split_full_name(full_name)
        office_phones = _combine_field_rows_by_type('office', 'number',
                                                    self._row('K'), self._row('BE'),
                                                    self._row('BF'), self._row('BI'))
        home_phones = _combine_field_rows_by_type('home', 'number',
                                                  self._row('M'), self._row('AK'),
                                                  self._row('CE'), self._row('CF'))
        fax_phones = _combine_field_rows_by_type('fax', 'number',
                                                 self._row('L'), self._row('CG'))
        phones = office_phones + home_phones + fax_phones
        emails = _combine_field_rows_by_type('office', 'email',
                                             self._row('AO'), self._row('BD'))
        # set and save attributes
        contact.company = company
        if title:  # give title precedence to titles within the first_name
            contact.title = title
        else:
            contact.title = _get_title_from_display(self._row('Q'))
        contact.suffix = self._row('D')
        contact.customer_id = self._row('B')
        contact.first_name = first_name
        contact.last_name = last_name
        contact.phones = phones
        contact.emails = emails

        # workflowlevel2_uuid
        if not contact.workflowlevel2_uuids:
            contact.workflowlevel2_uuids = [self._create_workflowlevel2(), ]

        contact.save()

        if created:
            print(f"{self.counter}: Contact with uuid={contact_uuid} created.")
        else:
            print(f"{self.counter}: Contact with uuid={contact_uuid} updated.")

        return contact.siteprofile_uuids, contact.workflowlevel2_uuids[0]

    def _import_siteprofile(self, site_profile_uuids, wfl2_uuid):
        """
        If there is no data in BJ, BK, BL, then G, I, J are “object_with_billing”
        If there is data in BJ, BK, BL, then it is saved as “object” and
        G, I, J are saved as “billing”.

        G - street & house number
        I - post address
        J - City

        site_profile_uuid in contact is the billing address (must also have a wfl2_uuid)
        object address needs only wfl2_uuid

        site_profile_uuids[0] is per definition the billing-address
        site_profile_uuids[1] is the object-address
        """
        billing_address_data = {
            'name': f"{self._row('G')}, {self._row('I')} {self._row('J')}",
            'address_line1': self._row('G'),
            'postcode': self._row('I'),
            'city': self._row('J')
        }
        billing_site_profile_uuid, object_site_profile_uuid = None, None
        if site_profile_uuids:
            billing_site_profile_uuid = site_profile_uuids[0]
            if len(site_profile_uuids) > 1:
                object_site_profile_uuid = site_profile_uuids[1]
        if (self._row('BJ'), self._row('BK'), self._row('BL')) == ('', '', ''):  # additional_address
            billing_site_profile_uuid = self._save_site_profile('object_with_billing', billing_address_data, wfl2_uuid,
                                                                billing_site_profile_uuid)
            print(f'SiteProfile for object_with_billing {billing_site_profile_uuid}.')
            return [billing_site_profile_uuid, ]
        else:
            billing_site_profile_uuid = self._save_site_profile('billing', billing_address_data, wfl2_uuid,
                                                                billing_site_profile_uuid)
            object_address_data = {
                # 'name': self._row('BJ'),  # import this later when we have a different structure
                'name': f"{self._row('BK')}, {self._row('BL')} {self._row('BM')}",
                'address_line1': self._row('BK'),
                'postcode': self._row('BL'),
                'city': self._row('BM'),
            }
            object_site_profile_uuid = self._save_site_profile('object', object_address_data, wfl2_uuid,
                                                               object_site_profile_uuid)
            print(f'SiteProfile for billing {billing_site_profile_uuid}, for object {object_site_profile_uuid}.')
            return billing_site_profile_uuid, object_site_profile_uuid

    def _set_site_profile_uuid_on_contact(self, site_profile_uuids):
        """Get contact_uuid and set site_profile_uuids on contact."""
        contact_uuid = self._row('A')
        qs = Contact.objects.filter(uuid=contact_uuid)
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

    def _get_date_from_row(self, value):
        """Check for date in self._row('AD') (year, date, only first product)."""
        if any(char.isdigit() for char in value) and len(value) == 4:
            value = f"01.01.{value}"
        date_format = '%d.%m.%Y'
        try:
            value = datetime.datetime.strptime(value, date_format)
        except ValueError:
            return None
        return str(value)

    def _update_product(self, product_uuid, product_data):
        url_update_product = URL_BIFROST + f'products/products/{product_uuid}'
        response = requests.patch(url_update_product, headers=self.headers, data=json.dumps(product_data))
        if response.status_code == 200:
            print(f"Product with uuid=product_uuid updated.")
        else:
            print(f"Error when updating Product with uuid=product_uuid.")
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
        product_names = (self._row('AE'), self._row('AF'), self._row('AG'),
                         self._row('AH'), self._row('AI'), self._row('AJ'))
        initial_product_data = {
            'workflowlevel2_uuid': wfl2_uuid,
        }
        installation_date = self._get_date_from_row(self._row('AD'))
        for i, product_name in enumerate(product_names):
            if product_name:
                product_uuid = self._check_product_existence(wfl2_uuid, product_name)
                product_data = {'name': product_name, **initial_product_data}
                if i == 0 and installation_date:
                    product_data['installation_date'] = installation_date
                if product_uuid:
                    self._update_product(product_uuid, product_data)
                else:
                    self._create_product(product_data)

    def parse_file(self, csv_path):

        with open(csv_path, 'rt') as csvfile:
            next(csvfile)  # skip first line
            for row in csv.reader(csvfile, delimiter=str(";"), dialect=csv.excel_tab):
                self.row = row
                if not self._row('A'):
                    continue
                self.counter += 1
                site_profile_uuids, wfl2_uuid = self._import_contact()
                site_profile_uuids = self._import_siteprofile(site_profile_uuids, wfl2_uuid)
                self._set_site_profile_uuid_on_contact(site_profile_uuids)
                self._import_product(wfl2_uuid)
        print(f"{self.counter} contacts parsed.")

    def handle(self, *args, **options):
        file = options.get('file', DEFAULT_FILE_NAME)
        csv_path = os.path.join(settings.BASE_DIR, '..', 'data', 'crm_service', file)
        print(f"Import data from {file}.")
        self.parse_file(csv_path)
