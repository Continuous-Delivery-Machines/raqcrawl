import tempfile
import unittest

from hamcrest import *

from TaskExecutor import TaskExecutor
from matchers.FileMatchers import *


class TaskExecutorTests(unittest.TestCase):

    def setUp(self):
        self.__tfile = tempfile.NamedTemporaryFile()
        self.__tdir = tempfile.mkdtemp()

    def tearDown(self):
        self.__tfile.close()
        os.rmdir(self.__tdir)

    def test_task_executor_init_restrictions_on_bad_path(self):
        assert_that(calling(TaskExecutor).with_args(None, 'asd$%&asd'), raises(IOError))

    def test_task_executor_init_restrictions_on_not_existing_path(self):
        assert_that(calling(TaskExecutor).with_args(None, '/x/x/x'), raises(IOError))

    def test_task_executor_init_restrictions_on_not_file_path(self):
        temp = tempfile.NamedTemporaryFile()
        assert_that(temp.name, is_path_to_file())
        assert_that(calling(TaskExecutor).with_args(None, temp.name), raises(IOError))

    def test_task_executor_init_restrictions_on_valid_path(self):
        temp = tempfile.mkdtemp()
        assert_that(temp, is_path_to_dir())
        assert_that(calling(TaskExecutor).with_args(None, temp), not_(raises(IOError)))
