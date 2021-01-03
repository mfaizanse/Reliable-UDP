from socket import *
import sys
import os.path
import json
import time
import struct
import math
import crcmod
import crc16

#from BadNet0 import *
#from BadNet1 import *
#from BadNet2 import *
from BadNet5 import *
#from BadNet4 import *
#from BadNet5 import *


#Main
blksz = 1024
RUPHeaderFormat = 'I I H H H'
RUPHeaderSize = 14

if len(sys.argv) < 3:
	print 'Server Port No. missing in command line arguments'
	serverPort = raw_input('Enter Server Port No.: ')
	print 'File name missing in command line arguments'
	filename = raw_input('Enter File name: ')
elif len(sys.argv) < 2:
	print 'Server Port No. missing in command line arguments'
	filename = raw_input('Enter Server Port No.: ')
else:
	serverPort = sys.argv[1]
	filename = sys.argv[2]

ServerAddr = ('127.0.0.1',int(serverPort))
clientSocket = socket(AF_INET, SOCK_DGRAM) 


#**********************************************************

#MakeHeader func
def makeHeader(Seq, Ack, rwnd, cwnd, checksum):
	RUPHeader = [Seq,Ack, rwnd, cwnd, checksum]
	s = struct.Struct(RUPHeaderFormat)
	packed_header = s.pack(*RUPHeader)
	#print ("Header length : " + str(len(packed_header)))
	return packed_header

#Makepacket func
def makePacket(RUPHeader, Data):
	packet_packed = RUPHeader + Data;
	#print ("Packet length : " + str(len(packet_packed)))
	return packet_packed

#recv
def splitPacket(message):
	#message, ClientAddress = clientSocket.recvfrom(2048) # get up to 1K at a time
	#print(message)
	s = struct.Struct(RUPHeaderFormat)
	RUPHeader = s.unpack(message[0:RUPHeaderSize])
	data = message[RUPHeaderSize:]
	return [RUPHeader,data]

#checkSum func
def checkSum(message):
	s = struct.Struct(RUPHeaderFormat)
	RUPHeader = s.unpack(message[0:RUPHeaderSize])
	d = message[RUPHeaderSize:]
	file = open('a', 'wb') # create local file in cwd
	file.write(d)
	file.close()
	file = open('a', 'rb') # create local file in cwd	
	d=file.read(blksz);
	file.close()	
	#print("\n",crc16.crc16xmodem(str(d) + str(RUPHeader[0]) + str(RUPHeader[1]) + str(RUPHeader[2]) + str(RUPHeader[3])),"   ",str(RUPHeader[4]),"\n")
	if(crc16.crc16xmodem(str(d) + str(RUPHeader[0]) + str(RUPHeader[1]) + str(RUPHeader[2]) + str(RUPHeader[3]))==(RUPHeader[4])):
		return 1
	else:
		return 0

def min(x1, x2):
	if x1<x2:
		return x1
	else:
		return x2

#--------------------------------------------------------------------
#sendFile func
def SendFile (filename):
	seqno = 0
	ackno = 0
	sendBase = 0
	nextSeqNo = 0
	counter = 0
	swndSize = 9 
	swnd = {}
	cwndSize = 1.0
	sendTime = -1
	timeout = 0.5
	startRetransmit = 0
	fileCompleted = 0
	sampleRTT = 0
	estimatedRTT = 0
	devRTT = 0
	retransmitted = 0

	#try:
	filepath = filename;
	#filepath = '/home/fzii97/cn/Client/PLT.pdf';
	file = open(filepath, 'rb')
	filesize = os.path.getsize(filepath)
	BadNet.transmit(clientSocket,str(filesize),ServerAddr[0],ServerAddr[1])
	#time.sleep(0.4)
	while 1:
		if nextSeqNo < (sendBase + min(swndSize,cwndSize)) and (counter < min(swndSize,cwndSize)) and fileCompleted != 1:
			fileData = file.read(blksz) # read from the file
			if fileData: # until file totally sent
				#print (str(nextSeqNo) , str(ackno) , str(swndSize), str(cwndSize))
				currentCheckSum= crc16.crc16xmodem(fileData + str(nextSeqNo) + str(ackno) + str(swndSize)+ str(int(cwndSize)))
				#print(currentCheckSum)
				header = makeHeader(nextSeqNo, ackno,swndSize,cwndSize, currentCheckSum)
				pkt = makePacket(header, fileData)
			
				BadNet.transmit(clientSocket,pkt,ServerAddr[0],ServerAddr[1])
				if nextSeqNo == sendBase:
					sendTime = time.time() #start timer if first
					retransmitted = 0
				swnd[str(nextSeqNo)] = pkt
				nextSeqNo = nextSeqNo + 1
				counter = counter + 1
				#print ("Sending new packet with seq = %d and counter is now",nextSeqNo-1, counter)
			else:
				fileCompleted = 1
		#if nextSeqNo == 2:
			#break
		if counter < min(swndSize,cwndSize):
			clientSocket.setblocking(0)
			try:
				message, ClientAddress = clientSocket.recvfrom(2048)
				#print ("non blocking Received..with seq = %d",nextSeqNo-1, counter)
				pktHeader,msg = splitPacket(message)
				#print ("--ack recv = ",pktHeader[1])
				if pktHeader[1] >= sendBase:
					if pktHeader[1] == sendBase and retransmitted != 1:
						sampleRTT = time.time()- sendTime
						estimatedRTT = 0.875*estimatedRTT + 0.125*sampleRTT;
						#devRTT = 0.75*devRTT + 0.25*abs(estimatedRTT - sampleRTT)
						timeout = estimatedRTT #+ 4*devRTT

					clientSocket.settimeout(None)
					#cwndSize = cwndSize + (1/math.floor(cwndSize))
					cwndSize = cwndSize + 1
					for i in range(sendBase, pktHeader[1]+1):
						counter = counter - 1
						#print ("--deleting pkt from swnd with seq = %d and counter is now %d and sendbase is ",i,counter,sendBase)
						del swnd[str(i)]
					sendBase = pktHeader[1] + 1
					#print ("--Sendbase is now "  ,sendBase)
			except:
				#print ("non blocking not received..with seq = %d",nextSeqNo-1, counter)
				message = ''
			clientSocket.setblocking(1)
		
		else:
			try:
				#print ("swnd limit")
				remainingTimeout = timeout - (time.time()- sendTime)
				if remainingTimeout <= 0:
					raise timeout
				clientSocket.settimeout(remainingTimeout)
				message, ClientAddress = clientSocket.recvfrom(2048)
				pktHeader,msg = splitPacket(message)
				
				#print ("ack recv = ",pktHeader[1])
				if pktHeader[1] >= sendBase:
					if pktHeader[1] == sendBase and retransmitted != 1:
						sampleRTT = time.time()- sendTime
						estimatedRTT = 0.875*estimatedRTT + 0.125*sampleRTT;
						devRTT = 0.75*devRTT + 0.25*abs(estimatedRTT - sampleRTT)
						timeout = estimatedRTT + 4*devRTT

					#cwndSize = cwndSize + (1/math.floor(cwndSize))
					cwndSize = cwndSize + 1
					clientSocket.settimeout(None)
					for i in range(sendBase, pktHeader[1]+1):
						counter = counter - 1
						#print ("deleting pkt from swnd with seq = %d and counter is now %d and sendbase is ",i,counter,sendBase)
						#print (swnd)
						del swnd[str(i)]
					sendBase = pktHeader[1] + 1
					#print ("Sendbase is now "  ,sendBase)
			except:
				startRetransmit = 1
				clientSocket.settimeout(None)

		if(time.time()- sendTime > timeout):
			startRetransmit = 1

		if startRetransmit == 1:
			startRetransmit = 0
			cwndSize = math.floor(cwndSize) / 2
			if cwndSize < 1:
				cwndSize = 1
			for pktseq in swnd.keys():
				#print ("--Pkt lost.. Retransmitting packet with seq = " , pktseq)
				BadNet.transmit(clientSocket,swnd[pktseq],ServerAddr[0],ServerAddr[1])
			sendTime = time.time() #start timer
			
		if fileCompleted == 1 and sendBase == nextSeqNo:
			break

	print("File Send: " + str(filesize) + " bytes")




#main
SendFile (filename)
print ("File Send")

clientSocket.close()


