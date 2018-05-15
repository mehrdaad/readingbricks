"""
Tests of functions that render HTML pages.

@author: Nikolay Lysenko
"""


import unittest
import os

from readingbricks import app
from readingbricks.db_control import DatabaseCreator
from readingbricks.markdown_notes_control import MarkdownDirectoryCreator


class TestViews(unittest.TestCase):
    """
    Tests of functions for rendering pages in HTML.
    """

    @classmethod
    def setUpClass(cls) -> type(None):
        """
        Do preparations that must be done once before all tests.
        """
        app.testing = True

        dir_path = os.path.dirname(__file__)
        ipynb_path = os.path.join(dir_path, 'resources/sample_notebooks')
        markdown_path = os.path.join(dir_path, 'markdown_notes')
        db_path = os.path.join(dir_path, 'tag_to_notes.db')
        counts_path = os.path.join(dir_path, 'resources/counts_of_tags.tsv')

        md_creator = MarkdownDirectoryCreator(ipynb_path, markdown_path)
        md_creator.create_or_update_directory_with_markdown_notes()
        db_creator = DatabaseCreator(ipynb_path, db_path)
        db_creator.create_or_update_db()

        app.config['path_to_ipynb_notes'] = ipynb_path
        app.config['path_to_markdown_notes'] = markdown_path
        app.config['path_to_db'] = db_path
        app.config['path_to_counts_of_tags'] = counts_path

    def setUp(self) -> type(None):
        """
        Do preparations that must be done before each test.
        """
        self.app = app.test_client()

    def test_home_page(self) -> type(None):
        """
        Test home page.
        """
        result = self.app.get('/').data.decode('utf-8')
        self.assertTrue('letters (4)' in result)
        self.assertTrue('digits (2)' in result)
        self.assertTrue('list (1)' in result)

    def test_default_page(self) -> type(None):
        """
        Test page that is shown when page is not found.
        """
        response = self.app.get('/non_existing')
        result = response.data.decode('utf-8')
        status_code = response.status_code
        self.assertTrue('<title>Страница не найдена</title>' in result)
        self.assertEqual(status_code, 404)

    def test_page_for_note(self) -> type(None):
        """
        Test page with a single note.
        """
        result = self.app.get('/notes/C').data.decode('utf-8')
        self.assertTrue('C:' in result)
        self.assertTrue('<li><p><em>c</em></p></li>' in result)
        self.assertTrue('<li><p>\\(c\\)</p></li>' in result)
        self.assertFalse('<h2>A</h2>' in result)
        result = self.app.get('/notes/non_existing').data.decode('utf-8')
        self.assertTrue('Страница не найдена.' in result)

    def test_page_for_tag(self) -> type(None):
        """
        Test page with all notes tagged with a specified tag.
        """
        result = self.app.get('/tags/digits').data.decode('utf-8')
        self.assertTrue('<h2>1</h2>' in result)
        self.assertFalse('<h2>A</h2>' in result)

        result = self.app.get('/tags/list').data.decode('utf-8')
        self.assertTrue('<h2>C</h2>' in result)
        self.assertFalse('<h2>A</h2>' in result)

        result = self.app.get('/tags/non_existing').data.decode('utf-8')
        self.assertTrue('Страница не найдена.' in result)

    def test_page_for_query_with_and(self) -> type(None):
        """
        Test POST requests made from a search bar of home page
        with AND operator.
        """
        query = 'list AND letters'
        response = self.app.post('/query', data={'query': query})
        result = response.data.decode('utf-8')
        self.assertTrue('C:' in result)
        self.assertTrue('<li><p><em>c</em></p></li>' in result)
        self.assertTrue('<li><p>\\(c\\)</p></li>' in result)
        self.assertFalse('<h2>1</h2>' in result)

        query = 'list AND digits'
        response = self.app.post('/query', data={'query': query})
        result = response.data.decode('utf-8')
        self.assertTrue('h2>Ничего не найдено</h2>' in result)

    def test_page_for_query_with_or(self) -> type(None):
        """
        Test POST requests made from a search bar of home page
        with OR operator.
        """
        query = 'list OR letters'
        response = self.app.post('/query', data={'query': query})
        result = response.data.decode('utf-8')
        self.assertTrue('<h2>A</h2>' in result)
        self.assertFalse('<h2>1</h2>' in result)
        self.assertTrue('<li><p><em>c</em></p></li>' in result)

        query = 'list OR digits'
        response = self.app.post('/query', data={'query': query})
        result = response.data.decode('utf-8')
        self.assertFalse('<h2>A</h2>' in result)
        self.assertTrue('<h2>1</h2>' in result)
        self.assertTrue('<li><p><em>c</em></p></li>' in result)

    def test_page_for_complex_query(self) -> type(None):
        """
        Test POST requests made from a search bar of home page
        with both AND and OR operators.
        """
        query = '(list AND letters) OR (digits AND letters)'
        response = self.app.post('/query', data={'query': query})
        result = response.data.decode('utf-8')
        self.assertTrue('<h2>C</h2>' in result)
        self.assertTrue('<li><p><em>c</em></p></li>' in result)
        self.assertFalse('<h2>B</h2>' in result)
        self.assertFalse('<h2>1</h2>' in result)

        query = '(list AND letters) AND ((digits OR letters OR list) OR list)'
        response = self.app.post('/query', data={'query': query})
        result = response.data.decode('utf-8')
        self.assertTrue('<h2>C</h2>' in result)
        self.assertTrue('<li><p><em>c</em></p></li>' in result)
        self.assertFalse('<h2>B</h2>' in result)
        self.assertFalse('<h2>1</h2>' in result)

        query = '(list AND letters) AND ((digits OR letters OR list) OR lists)'
        response = self.app.post('/query', data={'query': query})
        result = response.data.decode('utf-8')
        self.assertTrue('<h2>Запрос не может быть обработан</h2>' in result)


def main():
    test_loader = unittest.TestLoader()
    suites_list = []
    testers = [
        TestViews()
    ]
    for tester in testers:
        suite = test_loader.loadTestsFromModule(tester)
        suites_list.append(suite)
    overall_suite = unittest.TestSuite(suites_list)
    unittest.TextTestRunner().run(overall_suite)


if __name__ == '__main__':
    main()