#!/bin/bash

## This script simply cleans up Docker images without tag.
docker rmi --force $(docker images --filter "dangling=true" -q --no-trunc)
