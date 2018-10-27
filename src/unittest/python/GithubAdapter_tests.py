import unittest
from hamcrest import *
from GithubAdapter import GithubAdapter
import os

FORBIDDEN = '403 Forbidden'
OK = '200 OK'
UNAUTHORIZED = '401 Unauthorized'

RATE_REMAINING='X-RateLimit-Remaining'
RATE_LIMIT='X-RateLimit-Limit'

class GithubAdapterTest(unittest.TestCase):

    def setUp(self):
        self.__username = os.environ.get('RAQ_CRAWLER_TEST_USERNAME')
        self.__personal_access_token = os.environ.get('RAQ_CRAWLER_TEST_PAT')
        self.__env_stub = os.environ.get('RAQ_CRAWLER_TEST_STUB')

    def test_request_github_api_root(self):
        githubAdapter = GithubAdapter()
        body, headers = githubAdapter.requestApi('/')

        assert_that(headers, not_none())
        assert_that(headers["Status"], is_(any_of(OK, FORBIDDEN)))
        if headers["Status"] == OK:
            assert_that(int(headers[RATE_REMAINING]), is_(greater_than(0)))
        if headers["Status"] == FORBIDDEN:
            assert_that(int(headers[RATE_REMAINING]), is_(0))

    def test_request_current_sessions_user_unauthorized(self):
        githubAdapter = GithubAdapter()
        body, headers = githubAdapter.requestApi('/user')

        assert_that(headers, not_none())
        assert_that(headers["Status"], is_(any_of(UNAUTHORIZED, FORBIDDEN)))
        if headers["Status"] == UNAUTHORIZED:
            assert_that(int(headers[RATE_REMAINING]), is_(greater_than(0)))
        if headers["Status"] == FORBIDDEN:
            assert_that(int(headers[RATE_REMAINING]), is_(0))

    def test_authorization_via_user_request(self):
        githubAdapter = GithubAdapter()
        githubAdapter.set_credentials(personal_acess_token=self.__personal_access_token)
        body, headers = githubAdapter.requestApi('/user')

        assert_that(headers["Status"], is_("200 OK"))
        assert_that(int(headers[RATE_REMAINING]), is_(greater_than(0)))
        assert_that(body, has_entries())
        assert_that(body['login'], is_(self.__username))

    def test_os_environs_exist(self):
        assert_that(self.__env_stub, is_(not_none()))
        assert_that(self.__env_stub, is_("iamalive"))

