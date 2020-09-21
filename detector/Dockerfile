FROM registry.local/face_recognition:sixsq
RUN pip3 install pillow==4.0.0 requests
WORKDIR /root
ADD detector.py .
ENTRYPOINT ["python3", "/root/detector.py"]