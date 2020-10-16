#!/bin/bash

docker run -d --name=detector --net=host \
	-e CAPTURE_INTERVAL="60"   -e FRONTEND_SVC="frontend_svc:8080" \
	-e NODE_HOST="10.10.67.2" \
	registry.local/face_recognition_detector:rpc