import os
import unittest

from hamcrest import assert_that, not_none, any_of, is_, greater_than, has_entries, less_than, not_

from github_session import GithubSession
from raq_matchers.TimeMatchers import within_an_hour

OK = '200 OK'
UNAUTHORIZED = '401 Unauthorized'
FORBIDDEN = '403 Forbidden'

RATE_LIMIT = 'X-RateLimit-Limit'
RATE_REMAINING = 'X-RateLimit-Remaining'


class GithubSessionTest(unittest.TestCase):

    def setUp(self):
        self.__username = os.environ.get('RAQ_CRAWLER_TEST_GITHUB_USERNAME')
        self.__personal_access_token = os.environ.get('RAQ_CRAWLER_TEST_GITHUB_TOKEN')

    def test_request_github_api_root(self):
        github_session = GithubSession()
        _, headers = github_session.request_api('/')

        assert_that(headers, not_none())
        assert_that(headers["Status"], is_(any_of(OK, FORBIDDEN)))
        if headers["Status"] == OK:
            assert_that(int(headers[RATE_REMAINING]), is_(greater_than(0)))
        if headers["Status"] == FORBIDDEN:
            assert_that(int(headers[RATE_REMAINING]), is_(0))

    def test_request_current_sessions_user_unauthorized(self):
        github_session = GithubSession()
        _, headers = github_session.request_api('/user')

        assert_that(headers, not_none())
        assert_that(headers["Status"], is_(any_of(UNAUTHORIZED, FORBIDDEN)))
        if headers["Status"] == UNAUTHORIZED:
            assert_that(int(headers[RATE_REMAINING]), is_(greater_than(0)))
        if headers["Status"] == FORBIDDEN:
            assert_that(int(headers[RATE_REMAINING]), is_(0))

    def test_authorization_via_user_request(self):
        github_session = GithubSession()
        github_session.set_credentials(personal_access_token=self.__personal_access_token)
        body, headers = github_session.request_api('/user')

        assert_that(headers["Status"], is_("200 OK"))
        assert_that(int(headers[RATE_REMAINING]), is_(greater_than(0)))
        assert_that(body, has_entries())
        assert_that(body['login'], is_(self.__username))

    def test_rate_tracker_decrements(self):
        github_session = GithubSession()
        github_session.set_credentials(personal_access_token=self.__personal_access_token)
        github_session.request_api('/')
        rate_before = github_session.rate
        github_session.request_api('/')
        rate_after = github_session.rate

        assert_that(rate_after, is_(less_than(rate_before)))

    def test_rate_tracker_update_on_credential_change(self):
        github_session = GithubSession()
        github_session.request_api('/')
        rate_no_cred_after_req = github_session.rate
        github_session.set_credentials(personal_access_token=self.__personal_access_token)
        github_session.request_api('/')
        rate_with_cred_after_req = github_session.rate

        assert_that(rate_no_cred_after_req, is_(not_none()))
        assert_that(rate_with_cred_after_req, is_(not_none()))
        assert_that(rate_with_cred_after_req, is_(not_(rate_no_cred_after_req)))

    def test_rate_reset_timer_after_request(self):
        github_session = GithubSession()
        github_session.request_api('/')
        rate_reset_time_no_cred_after_req = github_session.rate_reset_time

        assert_that(rate_reset_time_no_cred_after_req, is_(not_none()))
        assert_that(rate_reset_time_no_cred_after_req, is_(within_an_hour()))
