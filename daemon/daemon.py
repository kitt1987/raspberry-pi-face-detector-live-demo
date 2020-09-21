import face_recognition
import io
import threading
import cv2
import os
import time
import requests
import docker
from dateutil.parser import parse

detectorIP = ''

def getContainerIP(hostnamePath, hostsPath):
    hostname = ''
    with open(hostnamePath, 'r') as file:
        hostname = file.read().rstrip()

    with open(hostsPath, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line.endswith(hostname):
                return line[:-1*len(hostname)].strip()

def getConcernedContainerIP():
    startedAt = 0
    hostnamePath = ''
    hostsPath = ''
    client = docker.from_env()
    for container in client.containers.list(filters={"ancestor": os.environ.get('TARGET_IMAGE')}):
        startTs = parse(container.attrs['State']['StartedAt']).timestamp()
        if startTs < startedAt:
            continue

        startedAt = startTs
        hostnamePath = container.attrs['HostnamePath']
        hostsPath = container.attrs['HostsPath']
        
    return getContainerIP(hostnamePath, hostsPath)

def scanDetector():
    while True:
        try:
            global detectorIP
            detectorIP = getConcernedContainerIP()
        except:
            pass
        time.sleep(5)
        

def detectLocally(frame):
    # Initialize some variables
    face_locations = []
    face_encodings = []
    face_names = []

    # Rotate 90 degrees
    #frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_small_frame)
    
    # Display the results
    text = ''
    for (top, right, bottom, left) in face_locations:
        text += '{},{},{},{},{}'.format(top*4, right*4, bottom*4, left*4, "Unknown")
        text += "\n"

    return text

def uploadAndDetect(image):
    if detectorIP == '':
        return ""

    try:
        url='http://{}/frame.jpg'.format(detectorIP)
        is_success, bytes = cv2.imencode(".jpg", image)
        r=requests.post(url,data=io.BytesIO(bytes), timeout=0.5)
        return r.text
    except:
        return detectLocally(image)

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

        detectResult = ''
        if process_this_frame:
            detectResult = uploadAndDetect(frame)

        process_this_frame = not process_this_frame

        if len(detectResult) > 0:
            for face in detectResult.splitlines():
                face = face.strip()
                if len(face) == 0:
                    continue
                pos = face.split(',')
                top = int(pos[0])
                right = int(pos[1])
                bottom = int(pos[2])
                left = int(pos[3])
                name = pos[4]
                # Display the results
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        cv2.namedWindow("Video", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Video",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
        # Display the resulting image
        cv2.imshow('Video', frame)

        # Hit any key to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # Release handle to the webcam
            video_capture.release()
            cv2.destroyAllWindows()
            os._exit(0)

if __name__ == '__main__':
    threading.Thread(target=scanDetector).start()
    capture()
