#!/bin/bash

## This script opens a shell in the first Docker image.
# This operation is very useful, as it allows to open the Docker
# container and execute arbitrary code or commands.  If a Python version
# is not specified, run the first image (pygasus-3.7 built on Python 3.7).
# Otherwise, run the specified image.

source "scripts/common.sh"

# Open a shell for the specified Python version.
#   arg1 -- the Python version as a string.
shell_one() {
  build_image_if_necessary "$1"
  docker run -v "/$(pwd):/usr/src/app" -it --rm "pygasus-$1" bash -c '
    python -VV | head -n 1
    bash'
}

# Open the specified shell, or a default one.
#   arg1 -- the Python version as a string or "first" to run the first version.
shell() {
  version=$1
  if [[ -z "$version" ]] || [[ "$version" == "first" ]]; then
    shell_one "${PYTHON_VERSIONS[0]}"
  else
    shell_one "$version"
  fi
}

if [ -n "${version-}" ]; then
  shell "$version"
else
  shell first
fi
