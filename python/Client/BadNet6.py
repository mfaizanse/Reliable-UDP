# FALL 2014 Computer Networks		SEECS NUST
# BESE 3
# Dr Nadeem Ahmed
# BadNet6:  a mix of drops, duplicates, errors and re-ordering of packets
# Usage: BadNet.transmit instead of sendto


from socket import *
import random
import time

class BadNet:

	dummy=' '
	reorder=0
	counter = 1
	error=1
	start=0
	
	@staticmethod
	def transmit(csocket,message,serverName,serverPort):
#		print 'Got a packet' + str(BadNet.counter)
		rand =random.random()
#Always drop the first 3 packet		
		if(BadNet.start<=2):
			print 'BadNet Dropped a packet' + str(BadNet.counter)
			BadNet.start=BadNet.start+1
			BadNet.counter=BadNet.counter+1	
			pass				
		else:	
		

			if rand >= 0.4:
				csocket.sendto(message,(serverName,serverPort))
#				print 'BadNet sends properly' + str(BadNet.counter)
	
			else:

				if rand >=0.3:
#					print 'BadNet Dropped a packet' + str(BadNet.counter)
					pass				
				

				elif rand>=0.2:
#					print 'BadNet creating packet errors' + str(BadNet.counter)
			
					mylist=list(message)
#				get last char of the string			
					x=ord(mylist[-1])
					if (x&1)==1:
						#if first bit set, unset it
						x &= ~(1)
					else:
						#if first bit not set, set it
						x |=  1
			
					mylist[-1]=chr(x)
					dummy=''.join(mylist)

					csocket.sendto(dummy,(serverName,serverPort))



				elif rand >=0.1:
#					print 'BadNet Duplicated a packet' + str(BadNet.counter)
					csocket.sendto(message,(serverName,serverPort))

					csocket.sendto(message,(serverName,serverPort))
			


				else:
					if BadNet.reorder == 1:
#						print 'BadNet re-ordering a packet' + str(BadNet.counter)
						csocket.sendto(message,(serverName,serverPort))
#						time.sleep(1)
						csocket.sendto(BadNet.dummy,(serverName,serverPort))
						BadNet.reorder=0
						BadNet.counter=BadNet.counter+1	
					else:
						BadNet.dummy=message
						BadNet.reorder=1
						BadNet.counter=BadNet.counter-1	






			BadNet.counter=BadNet.counter+1	





