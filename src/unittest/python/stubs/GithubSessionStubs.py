from typing import Tuple, MutableMapping, Mapping

from GithubSession import GithubSession
from stubs.StubExceptions import BadStubUsageException


class GithubSessionBaseStub(GithubSession):

    def __init__(self):
        super().__init__()

    @property
    def rate(self):
        raise BadStubUsageException()

    @property
    def rate_reset_time(self):
        raise BadStubUsageException()

    def request_api(self, path="/") -> Tuple[Mapping, MutableMapping]:
        raise BadStubUsageException()

    def set_credentials(self, personal_access_token: str) -> None:
        raise BadStubUsageException()
