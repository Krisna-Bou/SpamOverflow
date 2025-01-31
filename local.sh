#!/bin/bash

# Change to the app folder.
cd app

# # Buildkit to make sure we know what env
# export DOCKER_BUILDKIT=1

# Build the docker container.
docker build -t todo .

# Run the docker container in the background and remove after its closed.
docker run -d --rm -p 8080:8080 todo