.PHONY: daemon detector

PWD := $(shell pwd)

daemon:
	docker build -f ${PWD}/daemon/Dockerfile  -t registry.local/face_recognition_daemon:rpc ${PWD}

detector:
	docker build -f ${PWD}/detector/Dockerfile  -t registry.local/face_recognition_detector:rpc ${PWD}
