#!/bin/bash

docker run -d \
	-e FACE_DETECTION_SVC="domain:port" \
	registry.local/face_recognition_frontend:sixsq
