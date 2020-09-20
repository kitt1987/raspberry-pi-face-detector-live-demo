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
            detectorIP = getConcernedContainerIP()
        except:
            print('error on container scanning')
        time.sleep(5)
        

def uploadAndDetect(image):
    if detectorIP == '':
        return ""

    try:
        cv2.imwrite("frame", image)
        url='http://{}/frame'.format(detectorIP)
        files={'file': open('frame','rb')}
        r=requests.post(url,files=files)
        return r.text
    except:
        print("error arose when saving captures")
        return ""

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
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

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
                top = pos[0]
                right = pos[1]
                bottom = pos[2]
                left = pos[3]
                name = pos[4]
                # Display the results
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
    threading.Thread(target=scanDetector).start()
    capture()
