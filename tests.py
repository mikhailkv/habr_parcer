import unittest

from classes import FileHandler


class TestFileHandler(unittest.TestCase):

    def setUp(self) -> None:
        self.file_handler = FileHandler()

    def test_file_data(self):
        self.file_handler.read_file()
        for d in self.file_handler:
            self.assertTrue(d)
