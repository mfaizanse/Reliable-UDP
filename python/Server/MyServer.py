from socket import *
import os.path
import json
import sys
import time
import struct
import crcmod
import crc16

#from BadNet0 import *
#from BadNet1 import *
#from BadNet2 import *
from BadNet5 import *
#from BadNet4 import *
#from BadNet5 import *

#main
serverIP = '127.0.0.1'
blksz = 1024 #Bulk size for receiving file in chunks
RUPHeaderFormat = 'I I H H H'
RUPHeaderSize = 14

#CRC16 for Checksum
crc16_func = crcmod.mkCrcFun(0x11021, initCrc=0,rev=True, xorOut=0xFFFF)
checksum_correct=1

if len(sys.argv) < 2:
	print ('Server Port No. missing in command line arguments')
	serverPort = raw_input('Enter Server Port No.: ')
else:
	serverPort = sys.argv[1]

serverPort= int (serverPort)

#Creating server socket for control connection
serverSocket = socket(AF_INET, SOCK_DGRAM) 
serverSocket.bind((serverIP, serverPort))

#**********************************************************


#MakeHeader func
def makeHeader(Seq, Ack, rwnd, cwnd, checksum):
	#print (Ack)
	RUPHeader = [Seq,Ack, rwnd, cwnd, 4]
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
	#message, ClientAddress = serverSocket.recvfrom(2048) # get up to 1K at a time
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
	#print("\n",crc16.crc16xmodem(str(d) + str(RUPHeader[0]) + str(RUPHeader[1]) + str(RUPHeader[2])+ str(RUPHeader[3])),"   ",str(RUPHeader[4]),"\n")
	if(crc16.crc16xmodem(str(d) + str(RUPHeader[0]) + str(RUPHeader[1]) + str(RUPHeader[2]) + str(RUPHeader[3]))==(RUPHeader[4])):
		return 1
	else:
		return 0

#ReceiveFile func
def ReceiveFile():
	seqno = 0
	ackno = 0
	expectedSeqNo = 0
	#try:
	#filepath = filename
	filesize,ClientAddress = serverSocket.recvfrom(2048)
	#print(filesize)
	filesize = int(filesize)

	ReceivedBytes = 0
	file = open('testfile', 'wb') # create local file in cwd
	while True:
		message, ClientAddress = serverSocket.recvfrom(2048) # get up to 1K at a time

		#s = struct.Struct(RUPHeaderFormat)
		pktHeader,data = splitPacket(message)
		#print(checkSum(message))
		if expectedSeqNo == pktHeader[0] and checkSum(message):
			ReceivedBytes = ReceivedBytes + len(data);
			#print("Data len : " + str(len(data)))
			#print("ReceivedBytes len : " + str(ReceivedBytes))
			
			file.write(data) # write data in local file

			dat = ""
			header = makeHeader(0, pktHeader[0],0,0, crc16.crc16xmodem(str(dat) + str(0) + str(pktHeader[0]) +str(0)+ str(0)))
			#print ("Sending ack with " , pktHeader[0])
			
			pkt = makePacket(header, dat)
			BadNet.transmit(serverSocket,pkt,ClientAddress[0],ClientAddress[1])
			#BadNet.transmit(pkt,ClientAddress)
			expectedSeqNo = expectedSeqNo + 1
			if ReceivedBytes==filesize:
				break # till file received fully
		else:
			dat = ""
			header = makeHeader(0, expectedSeqNo-1,0,0, crc16.crc16xmodem(str(dat) + str(0) + str(pktHeader[0]) +str(0)+ str(0)))
			#print ("Sending dup ack with " , expectedSeqNo-1)
			pkt = makePacket(header, dat)
			BadNet.transmit(serverSocket,pkt,ClientAddress[0],ClientAddress[1])
			
	file.close()
	print 'File Received.'
	return 0
	

#main
print 'FTP Server Started successfully.\n' 
while 1:
	print 'The server is Waiting for a client.'
	timeTaken=time.time()
	ReceiveFile()
	timeTaken=time.time()-timeTaken

	print("Time Taken is: ",timeTaken)
	print ("File recvd")
	break #********************************<------ REMOVE THIS AND TEST
	#except:
		#print 'Error: Connection lost.'
	
