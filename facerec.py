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
        print(self.headers)
        file_length = int(self.headers['Content-Length'])
        output = PurePosixPath('/tmp').joinpath(filename.name)
        with open(output, 'wb') as output_file:
            output_file.write(self.rfile.read(file_length))
        self.send_response(201, 'Created')
        self.end_headers()
        reply_body = 'Saved "%s"\n' % filename.with_suffix('')
        self.wfile.write(reply_body.encode('utf-8'))
        self.wfile.flush()
        imageEncoding = face_recognition.face_encodings(face_recognition.load_image_file(str(output)))[0]
        # with faceLock:
        known_face_encodings.append(imageEncoding)
        known_face_names.append(str(filename.with_suffix('')))


def httpServer():
    with socketserver.TCPServer(("", 80), HTTPRequestHandler) as httpd:
        httpd.serve_forever()

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

def capture():
    # Get a reference to webcam #0 (the default one)
    video_capture = cv2.VideoCapture(0)

    # Initialize some variables
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Rotate 90 degrees
        #frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
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
                    uploadCapture(frame)

                face_names.append(name)

        process_this_frame = not process_this_frame


        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('Video', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=httpServer).start()
    capture()
