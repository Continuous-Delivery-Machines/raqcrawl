#!/usr/bin/env bash

if [ -d ".giit" ]; then
  echo "Version gitdescribed"
elif [ -z ${CODEBUILD_RESOLVED_SOURCE_VERSION+x} ]; then
  echo "Version unknown"
else
  echo "Version codebuilded"
fi