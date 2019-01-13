import unittest

from hamcrest import *

from repository_task import RepositoryTask
from task_supplier import TaskSupplier
from stubs.TaskSupplierStubs import TaskSupplierStub


class StubsTests(unittest.TestCase):

    def test_buildability_of_task_supplier_stub(self):
        task = RepositoryTask("a", ["a"])
        task_supplier_stub = TaskSupplierStub(task)
        assert_that(isinstance(task_supplier_stub, TaskSupplier), is_(True))
        assert_that(task_supplier_stub.has_next_repository_task(), is_(True))
        assert_that(task_supplier_stub.pop_next_repository_task(), is_(task))
