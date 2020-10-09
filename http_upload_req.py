#!/usr/bin/env python

import requests

url = 'http://localhost/upload_frame'
files = {'file': open('obama.jpg', 'rb')}
r = requests.post(url, files=files)
