import os
import subprocess

from pybuilder.core import init, use_plugin, Author, Project, task


def current_git_version_tag():
    if os.environ.get("CODEBUILD_RESOLVED_SOURCE_VERSION") is not None:
        return "0.0.CB0-g" + os.environ.get("CODEBUILD_RESOLVED_SOURCE_VERSION")
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
version = current_git_version_tag()

default_task = "run_unit_tests"


@init
def dependencies(project: Project):
    project.depends_on_requirements('requirements.txt')
    project.build_depends_on_requirements('requirements-test.txt')


@init
def coverages(project: Project):
    project.set_property('coverage_break_build', True)
    project.set_property('coverage_threshold_warn', 100)
    project.set_property('coverage_branch_threshold_warn', 100)
    project.set_property('coverage_branch_partial_threshold_warn', 100)


def print_name():
    print(name)
