import threading
import face_recognition
import cv2
import numpy as np
import os
import time
import http.server as server
import socketserver
import requests
from pathlib import Path, PurePosixPath

# Create arrays of known face encodings and their names
# faceLock = threading.Lock()
known_face_encodings = []
known_face_names = []
lastCaptureTs = 0
captureInterval = int(os.environ.get('CAPTURE_INTERVAL'))

class HTTPRequestHandler(server.SimpleHTTPRequestHandler):
    def do_POST(self):
        filename = Path(os.path.basename(self.path))
        file_length = int(self.headers['Content-Length'])
        self.send_response(201, 'Created')
        self.end_headers()
        if str(filename) == 'frame.jpg':
            self.wfile.write(detect(self.rfile.read(file_length)).encode('utf-8'))
        else:
            output = PurePosixPath('/tmp').joinpath(filename.name)
            with open(str(output), 'wb') as output_file:
                output_file.write(self.rfile.read(file_length))
            imageEncoding = face_recognition.face_encodings(face_recognition.load_image_file(str(output)))[0]
            # with faceLock:
            known_face_encodings.append(imageEncoding)
            known_face_names.append(str(filename.with_suffix('')))


def httpServer():
    server = socketserver.TCPServer(("", 80), HTTPRequestHandler)
    server.serve_forever()

def uploadCapture(image):
    try:
        global lastCaptureTs
        global captureInterval
        now = time.time()
        if now < lastCaptureTs+captureInterval:
            return
        cv2.imwrite("target.jpg", image)
        lastCaptureTs = now
        frontend = os.environ.get('FRONTEND_SVC')
        if frontend is not None:
            url='http://{}/upload_frame'.format(frontend)
            files={'file': open('target.jpg','rb')}
            r=requests.post(url,files=files)
        print("captures a new frame")
    except:
        print("error arose when saving captures")

def detect(frameBytes):
    # Initialize some variables
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    # Grab a single frame of video
    #frame = cv2.imread(framePath)
    frame = cv2.imdecode(np.frombuffer(frameBytes, np.uint8), -1)

    # Rotate 90 degrees
    #frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []
    detected = False
    # with faceLock:
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        if len(known_face_encodings) == 0:
            name = "Unknown"
            face_names.append(name)
            continue

        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        # # If a match was found in known_face_encodings, just use the first one.
        # if True in matches:
        #     first_match_index = matches.index(True)
        #     name = known_face_names[first_match_index]

        # Or instead, use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            detected = True

        face_names.append(name)
    
    # Display the results
    text = ''
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        text += '{},{},{},{},{}'.format(top*4, right*4, bottom*4, left*4, name)
        text += "\n"

    if detected:
        uploadCapture(frame)

    return text

if __name__ == '__main__':
    httpServer()
