# a scrolling spectrogram demo
# this streams audio from the nao and shows the spectrogram in a scrolling display
# don't forget to set the IP address and port for your robot
# guy brown university of sheffield
# last edited on 17/9/2014

from time import sleep
import sys
import matplotlib.pyplot as plt
from naoaudio import AudioReceiver
from naoqi import ALBroker
import numpy as np

def main():

	NAO_IP = "192.168.1.104"
	NAO_PORT = 9559

	# figure
		
	fig,ax = plt.subplots(1,1)
	h = ax.imshow(np.random.rand(341,500),vmin=0.0,vmax=70.0,origin='lower')
	plt.show(block=False)

	# we need a broker object to handle subscription of one module to another
	# and it needs to stay in memory all the time the program is running
	# without this, the audioreceiver won't properly subscribe to the audio service
	
	myBroker = ALBroker("myBroker","0.0.0.0",0,NAO_IP,NAO_PORT) 

	# start the audio receiver going

	global myAudio
	myAudio = AudioReceiver("myAudio",NAO_IP,NAO_PORT)
	myAudio.start(1)
	
	# only stop if on ctrl-c
	
	try:
		while True:
			sleep(0.1)
			h.set_data(myAudio.specgram)
			plt.draw()

	except KeyboardInterrupt:
		print "Interrupted by user, shutting down"
		myBroker.shutdown()
		sys.exit(0)

# run it

if __name__ == "__main__":
    main()

