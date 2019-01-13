import repository_task
from task_supplier import TaskSupplier


class TaskSupplierStub(TaskSupplier):

    def __init__(self, task: repository_task):
        self.__task = task

    def pop_next_repository_task(self) -> repository_task:
        return self.__task

    def has_next_repository_task(self) -> bool:
        return True
