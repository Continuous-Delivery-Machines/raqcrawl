from requests import Session
from json import loads
from typing import MutableMapping, Mapping, Tuple

class GithubAdapter:

    def __init__(self):
        self.__session = Session()
        pass

    def requestApi(self, path : str) -> Tuple[MutableMapping, Mapping]:
        response = self.__session.get("https://api.github.com" + path)
        return response.headers, loads(response.text)

    def login(self, personal_acess_token : str):
        s = "token {0}".format(personal_acess_token)
        self.__session.headers.update({"Authorization": s})
        response = self.__session.get("https://api.github.com/user")
        return response.headers, loads(response.text)