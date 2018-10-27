from datetime import datetime, timedelta

from hamcrest.core.base_matcher import BaseMatcher


class WithinDatetimeMatcher(BaseMatcher):

    def __init__(self, lower_limit_datetime: datetime, upper_limit_datetime: datetime):
        self.__lowerLimit = lower_limit_datetime
        self.__upperLimit = upper_limit_datetime

    def _matches(self, item: datetime):
        return self.__lowerLimit <= item <= self.__upperLimit

    def describe_to(self, description):
        description.append_text('datetime between {0} and {1}'.format(self.__lowerLimit, self.__upperLimit))


def within_an_hour():
    low = datetime.utcnow() - timedelta(seconds=10)
    up = datetime.utcnow() + timedelta(hours=1, seconds=10)
    return WithinDatetimeMatcher(low, up)
