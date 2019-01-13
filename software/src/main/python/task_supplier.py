from abc import ABCMeta, abstractmethod

import repository_task


class TaskSupplier(metaclass=ABCMeta):

    @abstractmethod
    def pop_next_repository_task(self) -> repository_task:
        pass

    @abstractmethod
    def has_next_repository_task(self) -> bool:
        pass
