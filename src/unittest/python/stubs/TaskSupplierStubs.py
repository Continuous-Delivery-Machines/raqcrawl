import RepositoryTask
from TaskSupplier import TaskSupplier


class TaskSupplierStub(TaskSupplier):

    def __init__(self, task: RepositoryTask):
        self.__task = task

    def popNextRepositoryTask(self) -> RepositoryTask:
        return self.__task

    def hasNextRepositoryTask(self) -> bool:
        return True
