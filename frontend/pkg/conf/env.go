package conf

import (
	"os"
)

const (
	EnvFaceDetectionSvc = "FACE_DETECTION_SVC"
	EnvPageHome         = "PAGE_HOME"
	EnvPort             = "PORT"
)

func FaceDetectionSvc() string {
	return os.Getenv(EnvFaceDetectionSvc)
}

func Port() string {
	port := os.Getenv(EnvPort)
	if len(port) == 0 {
		port = ":80"
	}

	return port
}

func Home() string {
	home := os.Getenv(EnvPageHome)
	if len(home) == 0 {
		home = "/tmp"
	}
	return home
}
