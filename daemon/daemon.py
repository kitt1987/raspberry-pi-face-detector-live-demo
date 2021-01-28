import cv2
import numpy as np
from io import BytesIO
import traceback

import grpc
import sys
import os
from concurrent import futures
import threading
import time

sys.path.append("rpc")
import face_pb2
import face_pb2_grpc

if 'GRPC_HOST' in os.environ:
    _HOST = os.environ['GRPC_HOST']
else:
    _HOST = '0.0.0.0'

if 'GPRC_HOST' in os.environ:
    _PORT = os.environ['GRPC_HOST']
else:
    _PORT = '9900'

if 'GRPC_WORKER' in os.environ:
    _RPC_WORKER = int(os.environ['GRPC_WORKER'])
else:
    _RPC_WORKER = 2

if 'ROTATE' in os.environ:
    rotate = int(os.environ['ROTATE'])
else:
    rotate = 1

if 'LEFT' in os.environ:
    left = int(os.environ['LEFT'])
else:
    left = 0

if 'TOP' in os.environ:
    top = int(os.environ['TOP'])
else:
    top = 0
# Global value shared with multithreading
gframe = []
face_names = []
face_locations = []
isExit = False
called = 0


def encode_frame(pb_frame):
    # numpy to bytes
    nda_bytes = BytesIO()
    np.save(nda_bytes, pb_frame, allow_pickle=False)
    return nda_bytes


def decode_frame(nda_bytes):
    # bytes to numpy
    nda_bytes = BytesIO(nda_proto.ndarray)
    return np.load(nda_bytes, allow_pickle=False)


class FaceService(face_pb2_grpc.FaceServiceServicer):
    def GetFrame(self, request, context):
        global gframe
        try:
            frame_process = gframe

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_frame = frame_process[:, :, ::-1]

            byteFrame = encode_frame(rgb_frame).getvalue()

            return face_pb2.Frame(
                ID=request.ID,
                Rgb_small_frame=byteFrame,
                Status=face_pb2.STATUS_OK,
            )

        except Exception as ex:
            traceback.print_exc()

    def DisplayLocations(self, request, context):
        try:
            message = request
            global face_names
            global face_locations
            global called
            l_face_names = message.Face_names
            l_face_locations = []
            for i in range(0, len(message.Face_locations)):
                l_face_locations.append(tuple(message.Face_locations[i].Loc))
            # print(message.Face_locations)

            face_names = l_face_names
            face_locations = l_face_locations

            called = called + 1

            return face_pb2.LocationResponse(
                Status=face_pb2.STATUS_OK,
            )
        except grpc.RpcError as rpc_error_call:
            details = rpc_error_call.details()
            print("err='RPCError DisplayLocations'")
            print("errMore=\"" + details + "\"")
        except Exception as ex:
            traceback.print_exc()


def serve():
    print("start serving rpc")
    grpcServer = grpc.server(futures.ThreadPoolExecutor(max_workers=_RPC_WORKER))
    face_pb2_grpc.add_FaceServiceServicer_to_server(FaceService(), grpcServer)

    grpcServer.add_insecure_port("{0}:{1}".format(_HOST, _PORT))
    grpcServer.start()
    print("waiting for incomming connection at {0}:{1}".format(_HOST, _PORT))
    # grpcServer.wait_for_termination()
    while True:
        if isExit:
            print("stop rpc server!")
            break


def displayResult(frame_process):
    global face_locations
    global face_names
    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Draw a box around the face
        cv2.rectangle(frame_process, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame_process, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame_process, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
    return frame_process


# exit fullscreen will click by mouse
def onMouse(event, x, y, flags, param):
    print(x, y)


def capture1():
    try:
        global gframe
        # Get a reference to webcam #0 (the default one)
        video_capture = cv2.VideoCapture(0)

        # Initialize some variables
        process_this_frame = True

        cv2.namedWindow("Video", flags=1)  # cv2.WINDOW_AUTOSIZE)
        cv2.setWindowProperty("Video", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        # cv2.moveWindow("Video", left, top)

        while True:
            # Grab a single frame of video
            ret, frame = video_capture.read()
            # overturn the frame
            if rotate:
                frame = cv2.flip(frame, 1)
                frame = cv2.rotate(frame, rotate)

            if process_this_frame:
                gframe = frame

            frame = displayResult(frame)
            process_this_frame = not process_this_frame

            # Display the resulting image
            cv2.imshow('Video', frame)

            # Hit any key to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                # Release handle to the webcam
                video_capture.release()
                cv2.destroyAllWindows()
                global isExit
                isExit = True
                sys.exit()
    except Exception as ex:
        traceback.print_exc()
        sys.exit()


def ping():
    while True:
        global face_locations
        last = called
        time.sleep(3)
        if last == called:
            # print("connetion from client closed, clean face_location")
            face_locations = []


def run():
    threading.Thread(target=ping).start()
    threading.Thread(target=capture1).start()
    serve()


if __name__ == '__main__':
    run()
