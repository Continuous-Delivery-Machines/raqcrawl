from pybuilder.core import init, use_plugin, Author, Project
import subprocess
import os

def currentGitVersionTag():
    if os.environ.get("TRAVIS") == "true":
        return "0.0.TRAVIS0"
    exit_core, s = subprocess.getstatusoutput("git describe")
    if exit_core != 0:
        raise RuntimeError("Unable to get git version")
    return s


use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.coverage")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin('python.pycharm')

description = """
<Insert descriptive description here>
"""
authors = [Author('Marvin Lukas Wenzel', 'wenzel@th-brandenburg.de', ["Backend Guru"])]
name = 'raqcrawler'
license = 'Apache License, Version 2.0'
summary = 'Crawler for the R.A.Q. project.'
url = 'http://www.whatthecommit.com'
version = currentGitVersionTag()

default_task = "run_unit_tests"


@init
def initialize(project: Project):
    project.build_depends_on('mockito')
    project.build_depends_on('PyHamcrest')
    project.depends_on('requests')
