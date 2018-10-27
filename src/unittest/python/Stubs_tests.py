import unittest

from hamcrest import *

from matchers.MyMatchers import should_have_caused_an_exception
from stubs.GithubSessionStubs import GithubSessionBaseStub
from stubs.StubExceptions import BadStubUsageException


class StubsTests(unittest.TestCase):

    def test_github_session_base_stub_failures(self):
        gs_stub = GithubSessionBaseStub()
        assert_that(calling(gs_stub.request_api), raises(BadStubUsageException))
        assert_that(calling(gs_stub.set_credentials).with_args("Something"), raises(BadStubUsageException))
        try:
            assert_that(gs_stub.rate, should_have_caused_an_exception())
        except BadStubUsageException:
            pass
        try:
            assert_that(gs_stub.rate_reset_time, should_have_caused_an_exception())
        except BadStubUsageException:
            pass
