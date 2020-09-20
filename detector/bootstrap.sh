#!/bin/bash

docker run -d \
	-e CAPTURE_INTERVAL="30" -e FRONTEND_SVC="domain:port" \
	registry.local/face_recognition_detector:sixsq
