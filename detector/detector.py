import http.server as server
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from pathlib import Path, PurePosixPath
import face_recognition
import numpy as np
from io import BytesIO
import traceback
import grpc
import os
from multiprocessing import Process, Manager, cpu_count, set_start_method
import threading
import sys
import time

sys.path.append("rpc")
import face_pb2
import face_pb2_grpc

# Initialize some variables
if 'NODE_HOST' in os.environ:
    _HOST = os.environ['NODE_HOST']
else:
    _HOST = '0.0.0.0'

if 'GPRC_HOST' in os.environ:
    _PORT = os.environ['GRPC_HOST']
else:
    _PORT = '9900'

if 'DISTANCE' in os.environ:
    ideal_distance = os.environ['DISTANCE']
else:
    ideal_distance = 0.45

if 'HOSTNAME' in os.environ:
    name = os.environ['HOSTNAME']
else:
    name = 'default'

# Create arrays of known face encodings and their names
# faceLock = threading.Lock()
lastCaptureTs = 0
captureInterval = int(os.environ.get('CAPTURE_INTERVAL'))
client_pid = 0
known_face_encodings = []
known_face_names = []


def encode_frame(pb_frame):
    # numpy to bytes
    nda_bytes = BytesIO()
    np.save(nda_bytes, pb_frame, allow_pickle=False)
    return nda_bytes


def decode_frame(ndarray):
    # bytes to numpy
    nda_bytes = BytesIO(ndarray)
    return np.load(nda_bytes, allow_pickle=False)


def find_face(rgb_small_frame):
    # Find all the faces and face encodings in the current frame of video
    face_names = []
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        # Or instead, use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if np.mean(face_distances) <= ideal_distance:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                threading.Thread(target=uploadCapture, args=rgb_small_frame).start()
        else:
            name = "Unknown"
        # print("find_face {0}/{1}".format(name, face_distances))

        face_names.append(name)
    return face_locations, face_names


def send_message(stub, worker_id):
    while True:
        response = stub.GetFrame(face_pb2.FrameRequest(ID=str(worker_id)))
        if response.Error:
            print(response.Error)
            return

        face_locations, face_names = find_face(decode_frame(response.Rgb_small_frame))

        locations = []
        for i in range(0, len(face_locations)):
            lc = []
            for j in range(0, len(face_locations[i])):
                lc.append(face_locations[i][j])
            locations.append(face_pb2.Location(Loc=lc))
        print(locations)
        try:
            stub.DisplayLocations(face_pb2.Locations(
                ID=response.ID,
                Face_locations=locations,
                Face_names=face_names,
            ))
        except Exception as ex:
            traceback.print_exc()


class helper():
    def setVal(self, Global):
        helper.Global = Global

    def getVal(self):
        return helper.Global


# helper for send global values to rpc func
rpc_helper = helper()


def run():
    worker_num = 1
    # Global for sharing value within processes
    Global = Manager().Namespace()
    # Create arrays of known face encodings and their names
    # faceLock = threading.Lock()
    Global.known_face_encodings = []
    Global.known_face_names = []
    rpc_helper.setVal(Global)

    p = Process(target=client, args=(name + "_rpc_client", worker_num,))
    p.start()
    global client_pid
    client_pid = p.pid
    print("rpc_client start")
    httpServer()


def getVal():
    global known_face_encodings
    global known_face_names
    while True:
        time.sleep(1)
        Global = rpc_helper.getVal()
        known_face_encodings = Global.known_face_encodings
        known_face_names = Global.known_face_names
        # print("get val {0}".format(known_face_names))


def client(worker_id, worker_num):
    threading.Thread(target=getVal).start()
    with grpc.insecure_channel(_HOST + ':' + _PORT) as channel:
        stub = face_pb2_grpc.FaceServiceStub(channel)
        try:
            send_message(stub, worker_id)
        except StopIteration as si:
            print("StopIteration")
            traceback.print_exc()
        except Exception as ex:
            traceback.print_exc()


def uploadCapture(RGB_image):
    try:
        global lastCaptureTs
        global captureInterval
        now = time.time()
        if now < lastCaptureTs + captureInterval:
            return
        BGR_image = cv2.cvtColor(RGB_image, cv2.COLOR_RGB2BGR)
        cv2.imwrite("target.jpg", BGR_image)
        lastCaptureTs = now
        frontend = os.environ.get('FRONTEND_SVC')
        if frontend is not None:
            url = 'http://{}/upload_frame'.format(frontend)
            files = {'file': open('target.jpg', 'rb')}
            r = requests.post(url, files=files)
        print("captures a new frame")
    except:
        print("error arose when saving captures")


class HTTPRequestHandler(server.SimpleHTTPRequestHandler):
    def log_request(self, format, *args):
        return

    def do_POST(self):
        Global = rpc_helper.getVal()
        known_face_encodings = Global.known_face_encodings
        known_face_names = Global.known_face_names

        filename = Path(os.path.basename(self.path))
        file_length = int(self.headers['Content-Length'])
        if str(filename) == 'frame.jpg':
            # result = detect(self.rfile.read(file_length)).encode('utf-8')
            result = ''
            self.send_response(404, 'NotFound')
            self.end_headers()
            self.wfile.write(result)
        else:
            print("hattp called")
            output = PurePosixPath('/tmp').joinpath(filename.name)
            with open(str(output), 'wb') as output_file:
                output_file.write(self.rfile.read(file_length))
            imageEncoding = face_recognition.face_encodings(face_recognition.load_image_file(str(output)))[0]
            # with faceLock:
            known_face_encodings.append(imageEncoding)
            known_face_names.append(str(filename.with_suffix('')))
            Global.known_face_encodings = known_face_encodings
            Global.known_face_names = known_face_names
            print("http save {0}".format(known_face_names))
            self.send_response(201, 'Created')
            self.end_headers()


class MTHTTPServer(ThreadingMixIn, HTTPServer):
    pass


def httpServer():
    server = MTHTTPServer(("", 80), HTTPRequestHandler)
    print("httpServer start")
    server.serve_forever()


if __name__ == '__main__':
    run()
