import os

from github_session import GithubSession


class TaskExecutor:

    def __init__(self, session: GithubSession, baseDir: str):
        if not os.path.isdir(baseDir):
            raise IOError('The provided path "{}" is not an existing directory.'.format(baseDir))
        if not os.access(baseDir, os.W_OK):
            raise IOError('The provided directory "{}" seems to be unwriteable.'.format(baseDir))

        self.__gh_session = session
        self._base_dir = baseDir
