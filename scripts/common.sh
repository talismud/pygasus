#!/bin/bash

## This script contains common data and functions.
# It will most likely be imported by other scripts.

# Array of supported Python versions
# Ordering matters: first and last image will be used for specific tasks.
PYTHON_VERSIONS=(3.7 3.8 3.9 3.10)

# Check if this is a valid Python version.
#   arg1 -- the Python version to check, as a string.
# If it fails, displays a message and exits the script.
check_if_valid() {
  printf '%s\n' "${PYTHON_VERSIONS[@]}" | grep -q -F "$1"
  if [ $? -ne 0 ]; then
    echo "$1 isn't a supported Python version."
    exit 1
  fi
}

# Build the image, even if it already is built.
# This will attempt to pull the latest image from Docker Hub as well.
#   arg1 -- the Python version as a string.
build_image() {
  version=$1
  check_if_valid "$version"
  echo "Pulling the image for python:${version}-slim..."
  docker pull "python:${version}-slim"
  echo "Build pygasus-${version}..."
  docker build -t "pygasus-$version" --rm \
      --build-arg PYTHON_VERSION="$version" .
}

# Build the image only if it's not already built.
#   arg1 -- the Python version as a string.
build_image_if_necessary() {
  version=$1
  check_if_valid "$version"
  built=`docker image ls | grep -F pygasus-${version}`
  if [ -z "$built" ]; then
    build_image "$version"
  fi
}
