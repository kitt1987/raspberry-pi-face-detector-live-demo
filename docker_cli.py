#!/usr/bin/env python

import os
import docker
from dateutil.parser import parse

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

print(getConcernedContainerIP())