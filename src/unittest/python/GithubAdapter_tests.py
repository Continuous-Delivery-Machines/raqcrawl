import unittest
from hamcrest import *
from GithubAdapter import GithubAdapter
import os


class GithubAdapterTest(unittest.TestCase):

    def setUp(self):
        self.__username = os.environ.get('RAQ_CRAWLER_TEST_USERNAME')
        self.__personal_access_token = os.environ.get('RAQ_CRAWLER_TEST_PAT')

    def test_request_github_api_root(self):
        githubAdapter = GithubAdapter()
        headers, body = githubAdapter.requestApi('/')

        assert_that(headers, not_none())
        assert_that(headers["Status"], is_('200 OK'))
        assert_that(body, not_none())
        assert_that(body, has_entries())

    def test_request_current_sessions_user_unauthorized(self):
        githubAdapter = GithubAdapter()
        headers, body = githubAdapter.requestApi('/user')

        assert_that(headers, not_none())
        assert_that(headers["Status"], is_('401 Unauthorized'))
        assert_that(body, not_none())
        assert_that(body, has_entries())

    def test_authorization_via_user_request(self):
        githubAdapter = GithubAdapter()
        githubAdapter.set_credentials(personal_acess_token=self.__personal_access_token)
        headers, body = githubAdapter.requestApi('/user')

        assert_that(headers["Status"], is_("200 OK"))
        assert_that(body, not_none())
        assert_that(body, has_entries())

    def test_os_environs_exist(self):
        stub = os.environ.get('RAQ_CRAWLER_TEST_STUB')

        assert_that(stub, is_(not_none()))
        assert_that(stub, is_("iamalive"))
