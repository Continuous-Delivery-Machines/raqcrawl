#!/usr/bin/env bash
ARTIFACTS_FOLDER=/home/marvin/dev/systemintegration/raq/raqcrawl/artifacts
rm -rf ${ARTIFACTS_FOLDER}
pyb clean
./codebuild_build.sh -i python:3.6-stretch -e local.env -a $ARTIFACTS_FOLDER
unzip -l ${ARTIFACTS_FOLDER}/artifacts.zip
