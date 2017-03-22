import unittest
from mock import Mock, MagicMock

from api_server import *


class TestApiServer(unittest.TestCase):

    def setUp(self):
        pass

    def test_parse_command(self):
        result1 = parse_command(
            u'create-issue CID Bug "Do good stuff" "Because I\'m Good"'
        )
        result2 = parse_command(u'')
        self.assertEquals(result1, ['create-issue', 'CID', 'Bug', 'Do good stuff', "Because I\'m Good"])
        self.assertEquals(result2, [])

