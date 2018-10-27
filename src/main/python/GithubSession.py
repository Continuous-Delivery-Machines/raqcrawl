from datetime import datetime
from json import loads
from typing import MutableMapping, Mapping, Tuple

from requests import Session

RATE_REMAINING = 'X-RateLimit-Remaining'
RATE_LIMIT = 'X-RateLimit-Limit'
RATE_RESET = 'X-RateLimit-Reset'


class GithubSession:

    def __init__(self):
        self.__rate = None
        self.__rater_reset_time = None
        self.__session = Session()

    @property
    def rate(self):
        """Maximum rate of requests this GithubAdapter is able to
        send with its current configuration.

        Is None if the the rate is not definitely known."""
        return self.__rate

    @property
    def rate_reset_time(self):
        """Represents to maximum rate of requests this GithubAdapter is able to
        send with its current configuration.

        Is None if the the rate is not definitely known."""
        return self.__rater_reset_time

    def request_api(self, path="/") -> Tuple[Mapping, MutableMapping]:
        """Sends a get request against GitHub's API against the specified endpoint.
        Requires leading slash [/]."""

        response = self.__session.get("https://api.github.com" + path)
        json_body, headers = loads(response.text), response.headers
        self.__rate = int(headers[RATE_REMAINING])

        """The X-RateLimit-Reset header shows UTC [non-milli]seconds, which is exactly what datetime wants."""
        self.__rater_reset_time = datetime.utcfromtimestamp(int(headers[RATE_RESET]))

        return json_body, headers

    def set_credentials(self, personal_access_token: str) -> None:
        """Sets headers permanently, according to the given token, to identify itself to the GitHub API."""
        s = "token {0}".format(personal_access_token)
        self.__session.headers.update({"Authorization": s})
        self.__rate = None
        self.__rater_reset_time = None
