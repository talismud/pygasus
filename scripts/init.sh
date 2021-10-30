#!/bin/bash

## This script is called to initialize or update the pygasus-* images.
# Calling it will force-update the image, even if one already exists.
# Calling this script without specyfing version will run
# the initialization for all images, which might take some time.
source "scripts/common.sh"

# Initialize one image.
#   arg1 -- the Python version.
init_one() {
  build_image "$1"
}

# Run the initialization.
#   arg1 -- the Python version or "all" to init all.
init() {
  version=$1
  if [[ -z "$version" ]] || [[ "$version" == "all" ]]; then
    for version in ${PYTHON_VERSIONS[@]}; do
      init_one $version
    done
  else
    init_one $version
  fi
}

if [ -n "${version-}" ]; then
  init "$version"
else
  init all
fi
