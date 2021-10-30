#!/bin/bash

## This script provides functions to format the code using black.
# The Docker container being run by this script
# is the latest version (Python 3.10).
source "scripts/common.sh"

# Function to format the pygasus package.
format() {
  version="${PYTHON_VERSIONS[-1]}"
  docker run -v "/$(pwd):/usr/src/app" -it --rm \
      "pygasus-${version}" black pygasus
}

format
