#!/bin/bash

## Check the Python syntax of the pygasus project.
# This will run both black and flake8 in the most
# recent Docker image (currently pygasus-3.10, built on Python 3.10).

source "scripts/common.sh"

# Function to call the commands in a Docker container.
check_style() {
  version="${PYTHON_VERSIONS[-1]}"
  docker run -v "/$(pwd):/usr/src/app" -it --rm "pygasus-${version}" bash -c "black --check --diff pygasus; flake8 pygasus"
}

check_style
