# Written by Dr. Guy Brown
from naoqi import ALProxy, ALModule, ALBroker
import sys
import numpy as np

# Audio receiver - creates a remote naoqi module that receives audio data in a buffer
# and generates callbacks when the buffer is full

class AudioReceiver(ALModule):

	def __init__(self,moduleName,naoIP,naoPort,chanFlag):
		try:
			ALModule.__init__(self,moduleName)
			self.BIND_PYTHON(self.getName(),"callback")
			self.naoIP = naoIP
			self.naoPort = naoPort
			self.outfile = None
			self.chanFlag = chanFlag
		except BaseException, err:
			print "ERR: AudioReceiver: loading error:"
            
	def __del__(self):
		print("INF: AudioReceiver: cleaning everything")
		self.stop()

	def start(self):
		audio = ALProxy("ALAudioDevice",self.naoIP,self.naoPort)
        # all = 0, left = 1, right = 2, front = 3, rear = 4
		deinterleave = 0
		sampleRate = 16000
		if self.chanFlag==0:
			sampleRate = 48000
		audio.setClientPreferences(self.getName(),sampleRate,self.chanFlag,deinterleave) 
		audio.subscribe(self.getName())
		print "INF: AudioReceiver: started!"

	def stop(self):
		print "INF: AudioReceiver: stopping..."
		audio = ALProxy("ALAudioDevice",self.naoIP,self.naoPort)
		audio.unsubscribe(self.getName())       
        print "INF: AudioReceiver: stopped!"
        
	def processRemote(self,numChannels,samplesPerChannel,timeStamp,buffer):
		#print "channels=",numChannels," samples=",samplesPerChannel
		soundDataInterleaved = np.fromstring(str(buffer),dtype=np.int16)
		self.soundData = np.reshape(soundDataInterleaved,(numChannels,samplesPerChannel),'F')
		
