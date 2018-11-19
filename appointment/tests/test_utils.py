from unittest import TestCase
from ..utils import str_to_bool


class UtilsTests(TestCase):
    def test_str_to_bool(self):
        self.assertTrue(str_to_bool('1'))
        self.assertTrue(str_to_bool('t'))
        self.assertTrue(str_to_bool('true'))
        self.assertTrue(str_to_bool('yes'))

        self.assertFalse(str_to_bool(None))
        self.assertFalse(str_to_bool('f'))
        self.assertFalse(str_to_bool('false'))
        self.assertFalse(str_to_bool('no'))
