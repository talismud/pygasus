#!/bin/bash

## This script runs the test coverage in the first Docker image.
# This script allows to check the coverage of current tests.  The coverage
# check is run, by default, in the first image (Python 3.7) but
# this can be changed to run in a specific version.

source "scripts/common.sh"

# Run the coverage for the specified Python version.
#   arg1 -- the Python version as a string.
coverage_one() {
  build_image_if_necessary "$1"
  docker run -v "/$(pwd):/usr/src/app" -it --rm "pygasus-$1" bash -c '
    pytest --cov=pygasus tests -sq --no-header
    python -VV | head -n 1'
}

# Run the specified coverage, or a default one.
#   arg1 -- the Python version as a string or "first" to run the first version.
coverage() {
  version=$1
  if [[ -z "$version" ]] || [[ "$version" == "first" ]]; then
    coverage_one "${PYTHON_VERSIONS[0]}"
  else
    coverage_one "$version"
  fi
}

if [ -n "${version-}" ]; then
  coverage "$version"
else
  coverage first
fi
