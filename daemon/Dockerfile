FROM sixsq/opencv-python:latest-arm64
RUN pip3 install docker
WORKDIR /root
ADD daemon.py .
ENTRYPOINT ["python3", "/root/daemon.py"]