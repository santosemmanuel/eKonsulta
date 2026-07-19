import unittest

import app as app_module


class AppHelpersTest(unittest.TestCase):
    def test_build_pdf_url_uses_expected_static_path(self):
        with app_module.app.test_request_context('/'):
            url = app_module.build_pdf_url(7, 'sample.pdf')

        self.assertEqual(url, '/static/pdfs/user_7/output/sample.pdf')


if __name__ == '__main__':
    unittest.main()
