from naoqi import ALProxy, ALModule, ALBroker
from time import sleep
import sys
import numpy as np
import matplotlib.pyplot as plt
import pam
import almath
#from mpl_toolkits.axes_grid.anchored_artists import AnchoredText

# Audio receiver - creates a remote naoqi module that receives audio data in a buffer
# and generates callbacks when the buffer is full

class AudioReceiver(ALModule):

	def __init__(self,moduleName,naoIP,naoPort):
		try:
			ALModule.__init__(self,moduleName)
			self.BIND_PYTHON(self.getName(),"callback")
			self.naoIP = naoIP
			self.naoPort = naoPort
			self.outfile = None
		except BaseException, err:
			print "ERR: AudioReceiver: loading error:"
            
	def __del__(self):
		print("INF: AudioReceiver: cleaning everything")
		self.stop()

	def start(self):
		audio = ALProxy("ALAudioDevice",self.naoIP,self.naoPort)
        # all = 0, left = 1, right = 2, front = 3, rear = 4
		channelFlag = 0
		deinterleave = 0
		sampleRate = 48000
		audio.setClientPreferences(self.getName(),sampleRate,channelFlag,deinterleave) 
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
		
# end of audio receiver

def main():

	MAX_DELAY = 32 # samples
	NUM_SAME = 2 # turn to face when we have NUM_SAME consecutive location estimates that are the same
	MAX_MOTOR_SPEED = 0.2
	NAO_IP = "169.254.88.3" #"192.168.1.101"
	NAO_PORT = 9559
	tts = ALProxy("ALTextToSpeech",NAO_IP,NAO_PORT)
	
	# prepare robot for head movement
	
	motion = ALProxy("ALMotion",NAO_IP,NAO_PORT)
	#motion.setStiffnesses("Head",1.0)
	motion.setStiffnesses(["HeadYaw","HeadPitch"],[1.0,1.0])
	# sleep(1)
	# motion.setAngles("HeadYaw",[-90*almath.TO_RAD],MAX_MOTOR_SPEED)
	# sleep(1)
	
	

	# figure
	fig,ax = plt.subplots(4,1)
	axis1, = ax[0].plot(range(4096),np.linspace(-32768,32768,4096))
	axis2, = ax[1].plot(range(4096),np.linspace(-32768,32768,4096))
	axis3, = ax[2].plot(range(MAX_DELAY*2+1),np.linspace(0,1.1,MAX_DELAY*2+1))
	#axis3, = ax[2].plot(range(MAX_DELAY*2+1),np.linspace(0,1.1,MAX_DELAY*2+1))

	plt.show(block=False)

	same_count = 0
	same_index = 0


	# we need a broker object to handle subscription of one module to another
	# and it needs to stay in memory all the time the program is running
	
	myBroker = ALBroker("myBroker","0.0.0.0",0,NAO_IP,NAO_PORT) 


	# start the audio receiver going

	global myAudio
	myAudio = AudioReceiver("myAudio",NAO_IP,NAO_PORT)
	myAudio.start()
	
	#only stop if on ctrl-c
	delta = 2
	azimuth = range(-90,91, delta)
	itds = np.zeros(len(azimuth))
	index = 0
	
	motion.setAngles("HeadYaw",[-90*almath.TO_RAD],MAX_MOTOR_SPEED)
	sleep(1)

	try:
		#while True:
		for x in azimuth:
			motion.setAngles("HeadYaw",[x*almath.TO_RAD],MAX_MOTOR_SPEED)
			sleep(0.5)
			chan1 = myAudio.soundData[0,:]
			chan2 = myAudio.soundData[1,:]

			ccg = pam.cross_correlation(chan1,chan2,MAX_DELAY)
			ccg = pam.normalise(ccg)
			maxidx = np.argmax(ccg)
			
			# if maxidx==same_index:
			# 	same_count += 1
			# else:
			# 	same_index = maxidx
			# 	same_count = 0
				
			# if same_count==5:
			# 	print "SOUND DETECTED AT %d" % maxidx
			# 	angle = -(maxidx-MAX_DELAY)/float(MAX_DELAY)
			# 	#motion.setAngles("HeadYaw",angle,MAX_MOTOR_SPEED)
			# 	sleep(2.0)

			axis1.set_ydata(chan1)
			axis2.set_ydata(chan2)
			axis3.set_ydata(ccg)

			# Square each value in the samples array and sum them
			sigmaSquaredL = float(np.sum(np.square(chan1)))
			sigmaSquaredR = np.sum(np.square(chan2))

			ild = 10.0 * np.log10((sigmaSquaredL)/np.sum(sigmaSquaredR))
			ildText = 'ILD: %.4f' % ild
			itdText = 'ITD: %.4f' % maxidx
			print ildText
			print itdText
			
			itds[index] = maxidx
			print itds
			print azimuth

			ax[3].plot(azimuth[0:index], itds[0:index])
			#ax[2].annotate(ildText, xy=(53,1),xytext=(53,1))
			#ax[2].annotation.remove()
			index+=1
			plt.draw()
		
		while True:
			sleep(0.1)
			chan1 = myAudio.soundData[0,:]
			chan2 = myAudio.soundData[1,:]

			ccg = pam.cross_correlation(chan1,chan2,MAX_DELAY)
			ccg = pam.normalise(ccg)
			maxidx = np.argmax(ccg)

			axis1.set_ydata(chan1)
			axis2.set_ydata(chan2)
			axis3.set_ydata(ccg)

			# Square each value in the samples array and sum them
			sigmaSquaredL = float(np.sum(np.square(chan1)))
			sigmaSquaredR = np.sum(np.square(chan2))

			ild = 10.0 * np.log10((sigmaSquaredL)/np.sum(sigmaSquaredR))
			ildText = 'ILD: %.4f' % ild
			itdText = 'ITD: %.4f' % maxidx
			print ildText
			print itdText
			plt.draw()

			
	except KeyboardInterrupt:
		print "Interrupted by user, shutting down"
		motion.setStiffnesses(["HeadYaw","HeadPitch"],[0.0,0.0])
		sleep(1.0)
		myBroker.shutdown()
		sys.exit(0)

# run it

if __name__ == "__main__":
    main()

