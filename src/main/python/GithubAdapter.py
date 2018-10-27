from requests import Session
from json import loads
from typing import MutableMapping, Mapping, Tuple


RATE_REMAINING='X-RateLimit-Remaining'
RATE_LIMIT='X-RateLimit-Limit'

class GithubAdapter:

    def __init__(self):
        self.__rate = None
        self.__session = Session()

    @property
    def rate(self):
        """Represents to maximum rate of requests this GithubAdapter is able to
        send with its current configuration.

        Is None if the the rate is not definitely known."""
        return self.__rate

    def requestApi(self, path="/") -> Tuple[Mapping, MutableMapping]:
        """Sends a get request against GitHub's API against the specified endpoint.
        Requires leading slash [/]."""
        response = self.__session.get("https://api.github.com" + path)
        json_body, headers = loads(response.text), response.headers
        self.__rate = int(headers[RATE_REMAINING])
        return json_body, headers

    def set_credentials(self, personal_acess_token: str) -> None:
        """Sets headers permanently, according to the given token, to identify itself to the GitHub API."""
        s = "token {0}".format(personal_acess_token)
        self.__session.headers.update({"Authorization": s})
        self.__rate = None

