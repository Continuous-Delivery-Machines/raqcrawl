from pybuilder.core import init, use_plugin, Author, Project, task, before
from os import system

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.coverage")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin('python.pycharm')

authors = [Author('Marvin Lukas Wenzel', 'wenzel@th-brandenburg.de', ["Backend Guru"])]

description = """
<Insert descriptive description here>
"""

name = 'raqcrawler'
license = 'Apache License, Version 2.0'
summary = 'Crawler for the R.A.Q. project.'
url = 'www.whatthecommit.com'
version = '0.0.dev1'

default_task = "run_unit_tests"

@init
def initialize(project : Project):
    project.build_depends_on('mockito')
    project.build_depends_on('PyHamcrest')
    project.depends_on('requests')
