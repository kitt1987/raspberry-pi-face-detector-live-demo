package ws

import (
	"bytes"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"os"
)

func uploadFile(w http.ResponseWriter, r *http.Request, dest string) (filename string) {
	// Maximum upload of 10 MB files
	r.ParseMultipartForm(10 << 20)

	// Get handler for filename, size and headers
	file, handler, err := r.FormFile("file")
	if err != nil {
		fmt.Println("Error Retrieving the File")
		fmt.Println(err)
		return
	}

	defer file.Close()
	fmt.Printf("Uploaded File: %+v\n", handler.Filename)
	fmt.Printf("File Size: %+v\n", handler.Size)
	fmt.Printf("MIME Header: %+v\n", handler.Header)

	filename = handler.Filename

	// Create file
	dst, err := os.Create(dest)
	defer dst.Close()
	if err != nil {
		fmt.Println(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Copy the uploaded file to the created file on the filesystem
	if _, err := io.Copy(dst, file); err != nil {
		fmt.Println(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	fmt.Fprintf(w, "Successfully Uploaded File\n")
	return
}

func fileUploadRequest(uri string, params map[string]string, paramName, path, filename string) {
	buf, err := ioutil.ReadFile(path)
	if err != nil {
		fmt.Println(err)
		return
	}

	request, err := http.NewRequest("POST", uri+"/"+filename, bytes.NewReader(buf))
	if err != nil {
		fmt.Println(err)
		return
	}

	client := &http.Client{}
	resp, err := client.Do(request)
	if err != nil {
		fmt.Println(err)
		return
	}

	fmt.Println(resp.StatusCode)
	fmt.Println(resp.Header)
	resp.Body.Close()
}
