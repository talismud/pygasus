#!/bin/bash

## This script runs the tests in one or more Python versions.
# If a version is specified, run the tests in it.  Otherwise, run the tests
# in all supported Python versions.

source "scripts/common.sh"

# Run the tests in one image.
#   arg1 -- the Python version as a string.
test_one() {
  build_image_if_necessary "$1"
  docker run -v "/$(pwd):/usr/src/app" -it --rm "pygasus-$1" bash -c '
    python -VV | head -n 1
    pytest -sq --no-header tests'
}

# Run the tests in one or more image.
#   arg1 -- the Python version as a string or "all" to run all.
test() {
  version=$1
  if [[ -z "$version" ]] || [[ "$version" == "all" ]]; then
    failed=0
    for version in ${PYTHON_VERSIONS[@]}; do
      test_one "$version"
      if [ $? -ne 0 ]; then
        ((failed+=1))
      fi
    done

    # If any fails, stop here.
    if [ "$failed" -ne 0 ]; then
      echo "${failed} test suites failed."
      exit 1
    fi
  else
    test_one "$version"
  fi
}

if [ -n "${version-}" ]; then
  test "$version"
else
  test all
fi
