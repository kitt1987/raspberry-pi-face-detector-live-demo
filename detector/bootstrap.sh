#!/bin/bash

docker run -d --name=detector --net=host \
	-e CAPTURE_INTERVAL="60" -e FRONTEND_SVC="localhost:8080" \
	registry.local/face_recognition_detector:sixsq