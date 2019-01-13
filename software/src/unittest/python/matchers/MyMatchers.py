from hamcrest.core.base_matcher import BaseMatcher


class FailingMatcher(BaseMatcher):

    def __init__(self, msg: str):
        self.__msg = msg

    def _matches(self, item='Runnable code'):
        return False

    def describe_to(self, description):
        description.append_text(self.__msg)


def should_have_caused_an_exception():
    return FailingMatcher('to not even reach this line because of some exception')
