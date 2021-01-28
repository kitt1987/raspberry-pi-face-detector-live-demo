FROM registry.local/face_recognition-base:sixsq-rpc
WORKDIR /root
ADD daemon/daemon.py ./daemon/daemon.py
ADD rpc ./rpc
ENTRYPOINT ["python3", "-u", "/root/daemon/daemon.py"]
