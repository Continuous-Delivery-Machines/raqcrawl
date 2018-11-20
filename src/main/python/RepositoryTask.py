from typing import List


class RepositoryTask:

    def __init__(self, repo: str, requests: List):
        self.__repo = repo
        self.__requests = requests

    @property
    def repo(self):
        return self.__repo

    @property
    def requests(self):
        return self.requests
