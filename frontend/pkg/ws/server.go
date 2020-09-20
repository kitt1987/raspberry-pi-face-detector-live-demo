package ws

import (
	"github.com/git-roll/monkey2/pkg/conf"
	"github.com/git-roll/monkey2/pkg/util"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	uploadedFiles = "/tmp/uploaded"
	uploadedURL   = "/images"
	indexPage     = "page.html"
)

var (
	targetFile = filepath.Join(uploadedFiles, "target")
)

func updateFaceDetection(filename, path string) {
	fdSvc := conf.FaceDetectionSvc()
	if len(fdSvc) == 0 {
		return
	}

	fileUploadRequest("http://"+fdSvc, nil, "file", path, filename)
}

func uploadTargetHandler(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodPost {
		writer.WriteHeader(http.StatusNotFound)
		return
	}

	filename := uploadFile(writer, request, targetFile)
	updateFaceDetection(filename, targetFile)
}

func uploadFrameHandler(writer http.ResponseWriter, request *http.Request, ws io.WriteCloser) {
	if request.Method != http.MethodPost {
		writer.WriteHeader(http.StatusNotFound)
		return
	}

	frameName := "frame-" + time.Now().Format(time.RFC3339)
	uploadFile(writer, request, filepath.Join(uploadedFiles, frameName))
	ws.Write([]byte(uploadedURL + "/" + frameName))
}

func NewServer() *Server {
	os.MkdirAll(uploadedFiles, 0777)
	s := &Server{}
	ws := s.MonkeyNotifier()

	http.HandleFunc("/", func(writer http.ResponseWriter, request *http.Request) {
		if strings.HasPrefix(request.URL.Path, uploadedURL) {
			http.ServeFile(writer, request, filepath.Join(uploadedFiles, filepath.Base(request.URL.Path)))
			return
		}

		switch request.URL.Path {
		case "/upload_target":
			uploadTargetHandler(writer, request)
		case "/upload_frame":
			uploadFrameHandler(writer, request, ws)
		default:
			http.ServeFile(writer, request, filepath.Join(conf.Home(), indexPage))
		}
	})

	lis, err := net.Listen("tcp", conf.Port())
	if err != nil {
		panic(err)
	}

	s.lis = lis
	return s
}

type Server struct {
	lis net.Listener
}

func (s *Server) MonkeyNotifier() io.WriteCloser {
	writer := newWSWriter()
	http.Handle("/monkey", writer)
	return writer
}

func (s *Server) Run(stopC <-chan struct{}) {
	done := util.Start(func() {
		http.Serve(s.lis, nil)
	})

	<-stopC
	s.lis.Close()
	<-done
}
