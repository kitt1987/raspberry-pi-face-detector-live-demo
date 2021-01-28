FROM registry.local/face_recognition-base:sixsq-rpc
WORKDIR /root
ADD detector/detector.py ./detector/detector.py
ADD rpc ./rpc
ENTRYPOINT ["python3", "-u", "/root/detector/detector.py"]

