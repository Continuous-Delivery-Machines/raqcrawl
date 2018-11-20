import os

from hamcrest.core.base_matcher import BaseMatcher


class CallableMatcher(BaseMatcher):

    def __init__(self, x, msg: str, reverseOutcome=False):
        self.__reverse = reverseOutcome
        self.__x = x
        self.__msg = msg

    def _matches(self, item: str):
        if self.__reverse:
            return not self.__x(item)
        return self.__x(item)

    def describe_to(self, description):
        description.append_text(self.__msg)


def is_path_to_dir():
    return CallableMatcher(os.path.isdir, 'a path to a directory')


def is_path_to_file():
    return CallableMatcher(os.path.isfile, "a path to a file")


def is_path_to_nothing():
    return CallableMatcher(os.path.exists, "a path leads to nothing", reverseOutcome=True)
