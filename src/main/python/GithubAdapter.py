from requests import Session
from json import loads
from typing import MutableMapping, Mapping, Tuple


class GithubAdapter:

    def __init__(self):
        self.__session = Session()
        pass

    def requestApi(self, path="/") -> Tuple[Mapping, MutableMapping]:
        """Sends a get request against GitHub's API against the specified endpoint.
        Requires leading slash [/]."""
        response = self.__session.get("https://api.github.com" + path)
        return loads(response.text), response.headers

    def set_credentials(self, personal_acess_token: str) -> None:
        """Sets headers permanently, according to the given token, to identify itself to the GitHub API."""
        s = "token {0}".format(personal_acess_token)
        self.__session.headers.update({"Authorization": s})
