.PHONY: bin

PWD := $(shell pwd)
SHELL:=/bin/bash

bin:
	go build -p 4 -o $(PWD)/_output/monkey

linux:
	GOOS=linux GOARCH=amd64 $(MAKE)

monkey: linux
	@docker build -f hack/Dockerfile -t registry.local/face_recognition_frontend:sixsq .
