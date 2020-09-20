package main

import (
	"github.com/git-roll/monkey2/pkg/ws"
	"k8s.io/apimachinery/pkg/util/wait"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	signCh := make(chan os.Signal, 3)
	signal.Ignore(syscall.SIGPIPE)
	signal.Notify(signCh, syscall.SIGSEGV, syscall.SIGINT, syscall.SIGHUP, syscall.SIGTERM)

	wss := ws.NewServer()

	stopC := make(chan struct{})
	wg := wait.Group{}
	wg.StartWithChannel(stopC, wss.Run)
	<-signCh
	close(stopC)
	wg.Wait()
}
