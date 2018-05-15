import unittest
from RepoOps import RepoOps

# Test Token
TEST_TOKEN = "b80657ee0cc2dd126a728c0391049ebdeff2718b"


class TestIntegerBreak(unittest.TestCase):

    def setUp(self):
        self.repo = RepoOps(TEST_TOKEN)
        self.repo.get_user_repo('homework')

    def tearDown(self):
        self.repo = None

    def test_case_3(self):
        self.assertEqual(
            True,
            self.repo.get_org_repo(
                'SlackRecruiting', 'br-code-exercise-73939156'))

    def test_case_4(self):
        self.assertRaises(
            Exception,
            self.repo.get_org_repo(
                'SlackRecruiting', 'br-code-exercise-12345'))

    def test_case_5(self):
        self.assertEqual(
            ['beer', '1.1'],
            self.repo.get_next_release_info('apple'))

    def test_case_6(self):
        self.assertRaises(
            Exception,
            self.repo.get_next_release_info('greg'))

    def test_case_7(self):
        self.assertEqual(
            ['apple', '1.0'],
            self.repo.get_last_release_info('beer'))

    def test_case_8(self):
        self.assertEqual(
            [0, 0],
            self.repo.get_last_release_info('apple'))

    def test_case_9(self):
        self.assertEqual(
            True,
            self.repo.generate_feature_report('apple', 'cake'))

    def test_case_10(self):
        self.assertEqual(
            True,
            self.repo.generate_feature_report(0, 'apple'))

if __name__ == '__main__':
    unittest.main()
