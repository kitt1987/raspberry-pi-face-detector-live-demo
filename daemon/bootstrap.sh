#!/bin/bash

docker run -d --name="video-daemon" --restart=always --net=host --privileged \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	-v /root/.Xauthority:/root/.Xauthority \
	-e DISPLAY=":0.0" -e QT_X11_NO_MITSHM=1 -e QT_GRAPHICSSYSTEM="native" -e TARGET_IMAGE="registry.local/face_recognition_detector" \
	--device="/dev/video0:/dev/video0" \
	registry.local/face_recognition_daemon:sixsq
