# -*- coding: utf-8 -*-
import uuid

from django.test import TestCase
from django.apps import apps
from crm.apps import CrmConfig

from .. import gunicorn_conf


class TestGunicornConf(TestCase):
    def setUp(self):
        self.user = uuid.uuid4()

    def test_config_values(self):
        self.assertEqual(gunicorn_conf.bind, '0.0.0.0:80')
        self.assertEqual(gunicorn_conf.limit_request_field_size, 0)
        self.assertEqual(gunicorn_conf.limit_request_line, 0)


class CrmConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(CrmConfig.name, 'crm')
        self.assertEqual(apps.get_app_config('crm').name, 'crm')
