import csv
import os
import string

from django.conf import settings
from django.core.management.base import BaseCommand

from contact.models import Contact, TITLE_CHOICES

DEFAULT_FILE_NAME = 'TopKontor_Ritz.csv'


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
    title_displays = [y[1] for y in TITLE_CHOICES]
    if title_display in title_displays:
        title_index = title_displays.index(title_display)
        return TITLE_CHOICES[title_index][0]
    return None


def _combine_field_rows_by_type(_type, field_name, *row_fields):
    field_value = []
    for row in row_fields:
        if row:
            field_value.append({'type': _type, field_name: row})
    return field_value


class Command(BaseCommand):
    help = """
    Import CSV from a file.
    """

    row_map = dict()

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

    def add_arguments(self, parser):
        parser.add_argument(
            'file', default=None, nargs='?',
            help='Path of file to import.',
        )

    def handle(self, *args, **options):
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

        file = getattr(options, 'file', DEFAULT_FILE_NAME)

        print(f"Import contacts from {file}.")

        counter = 0
        csv_path = os.path.join(settings.BASE_DIR, '..', 'data', 'crm_service', file)

        # organization_uuid = 'fd383104-20fa-4156-93c0-fe75d10005ab'  # Ritz GmbH on production
        # workflowlevel1_uuid = '6a4c8b6e-f90b-4554-b092-9a3a77bc00de'  # WorkflowLevel1.objects.get(name='Ritz GmbH').level1_uuid on production  # noqa
        organization_uuid = '460c0ed6-445b-4204-8a6e-442ebb8b97a9'  # Test Import Organization on dev
        workflowlevel1_uuid = '7f69cdd8-11ac-421e-88a2-a2f0334109a3'  # Test Import Wfl1 on dev

        with open(csv_path, 'rt') as csvfile:
            next(csvfile)  # skip first line
            next(csvfile)  # skip also second line (descriptions)
            for row in csv.reader(csvfile, delimiter=str(";"), dialect=csv.excel_tab):
                contact_uuid = row[self.row_map['A']]
                if not contact_uuid:
                    continue
                # get or create contact by uuid
                counter += 1
                contact, created = Contact.objects.get_or_create(
                    uuid=contact_uuid,
                    defaults={'organization_uuid': organization_uuid,
                              'workflowlevel1_uuids': [workflowlevel1_uuid, ]}
                )

                # get attributes
                company = _merge_fields(row[self.row_map['D']], row[self.row_map['S']], row[self.row_map['F']])
                full_name = row[self.row_map['E']]
                title, first_name, last_name = _split_full_name(full_name)
                office_phones = _combine_field_rows_by_type('office', 'number',
                                                            row[self.row_map['K']], row[self.row_map['BE']],
                                                            row[self.row_map['BF']], row[self.row_map['BI']])
                home_phones = _combine_field_rows_by_type('home', 'number',
                                                          row[self.row_map['M']], row[self.row_map['AK']],
                                                          row[self.row_map['CE']], row[self.row_map['CF']])
                fax_phones = _combine_field_rows_by_type('fax', 'number',
                                                         row[self.row_map['L']], row[self.row_map['CG']])
                phones = office_phones + home_phones + fax_phones
                emails = _combine_field_rows_by_type('office', 'email',
                                                     row[self.row_map['AO']], row[self.row_map['BD']])
                # set and save attributes
                contact.company = company
                if title:  # give title precedence to titles within the first_name
                    contact.title = title
                else:
                    contact.title = _get_title_from_display(row[self.row_map['Q']])
                contact.first_name = first_name
                contact.last_name = last_name
                contact.phones = phones
                contact.emails = emails
                contact.save()

                if created:
                    print(f"Contact with {contact_uuid} created.")
                else:
                    print(f"Contact with {contact_uuid} updated.")

        print(f"%s contacts parsed." % counter)
