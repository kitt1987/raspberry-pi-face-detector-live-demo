#!/bin/bash

docker run -d --name=frontend --net=host \
	-e FACE_DETECTION_SVC="localhost" \
	-e PORT=8080 \
	registry.local/face_recognition_frontend:sixsq
