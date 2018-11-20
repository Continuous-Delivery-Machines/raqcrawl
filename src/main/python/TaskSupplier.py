from abc import ABCMeta, abstractmethod

import RepositoryTask


class TaskSupplier(metaclass=ABCMeta):

    @abstractmethod
    def popNextRepositoryTask(self) -> RepositoryTask:
        pass

    @abstractmethod
    def hasNextRepositoryTask(self) -> bool:
        pass
