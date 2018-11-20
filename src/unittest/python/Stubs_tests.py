import unittest

from hamcrest import *

from RepositoryTask import RepositoryTask
from TaskSupplier import TaskSupplier
from stubs.TaskSupplierStubs import TaskSupplierStub


class StubsTests(unittest.TestCase):

    def test_buildability_of_task_supplier_stub(self):
        task = RepositoryTask("a", ["a"])
        task_supplier_stub = TaskSupplierStub(task)
        assert_that(isinstance(task_supplier_stub, TaskSupplier), is_(True))
        assert_that(task_supplier_stub.hasNextRepositoryTask(), is_(True))
        assert_that(task_supplier_stub.popNextRepositoryTask(), is_(task))
