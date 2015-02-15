# scrolling spectrogram

from naoqi import ALProxy, ALModule, ALBroker
import numpy as np

# Audio receiver - creates a remote naoqi module that receives audio data in a buffer
# and generates callbacks when the buffer is full

class AudioReceiver(ALModule):

	def __init__(self,moduleName,naoIP,naoPort):
		try:
			ALModule.__init__(self,moduleName)
			self.BIND_PYTHON(self.getName(),"callback")
			self.naoIP = naoIP
			self.naoPort = naoPort
			self.specgram = np.zeros((341,300))
		except BaseException, err:
			print "ERR: AudioReceiver: loading error:"
            
	def __del__(self):
		print("INF: AudioReceiver: cleaning everything")
		self.stop()

	def start(self, channelFlag):
		audio = ALProxy("ALAudioDevice",self.naoIP,self.naoPort)
        # all = 0, left = 1, right = 2, front = 3, rear = 4
		#channelFlag = 1
		deinterleave = 0
		sampleRate = 16000
		audio.setClientPreferences(self.getName(),sampleRate,channelFlag,deinterleave) 
		#
		audio.subscribe(self.getName())
		audio.enableEnergyComputation()
		
		print "INF: AudioReceiver: started!"

	def stop(self):
		print "INF: AudioReceiver: stopping..."
		audio = ALProxy("ALAudioDevice",self.naoIP,self.naoPort)
		audio.unsubscribe(self.getName()) 
        print "INF: AudioReceiver: stopped!"

	def computeEnergy(self, channel):
		audio = ALProxy("ALAudioDevice",self.naoIP,self.naoPort)

		if channel==1:
			return audio.getLeftMicEnergy()	
		else:
			return audio.getRightMicEnergy()
	
	def processRemote(self,numChannels,samplesPerChannel,timeStamp,buffer):
		#print "channels=",numChannels," samples=",samplesPerChannel
		soundData = np.fromstring(str(buffer),dtype=np.int16)
		mag = np.abs(np.fft.rfft(soundData * np.hanning(soundData.size)))
		mag = np.power((mag[0:mag.size/2]),0.3)
		self.specgram = np.roll(self.specgram,1,axis=1)
		self.specgram[:,0]=mag
		
# end of audio receiver



