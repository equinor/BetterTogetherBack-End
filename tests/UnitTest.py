import unittest


class UnitTest(unittest.TestCase):

    def test_fail(self):
        self.assertEqual(1, 2)


if __name__ == '__main__':
    unittest.main()
