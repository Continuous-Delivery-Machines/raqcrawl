from pybuilder.core import init, use_plugin, Author, Project, task

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.coverage")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin('python.pycharm')

authors = [Author('Marvin Lukas Wenzel', 'wenzel@th-brandenburg.de', ["Backend Guru"])]
name = 'raq-crawler'
version = "WIP"
license = 'Apache License, Version 2.0'
summary = 'Crawler for the R.A.Q. project.'
url = 'http://www.whatthecommit.com'


@init
def dependencies(project: Project):
    project.depends_on_requirements('requirements.txt')
    project.build_depends_on_requirements('requirements-dev.txt')


@init
def coverages(project: Project):
    project.set_property('coverage_break_build', False)
    project.set_property('coverage_threshold_warn', 70)
    project.set_property('coverage_branch_threshold_warn', 70)
    project.set_property('coverage_branch_partial_threshold_warn', 70)
