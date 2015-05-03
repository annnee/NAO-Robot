# Written by Dr. Guy Brown and Ann Nee Lau
from naoqi import ALProxy, ALModule, ALBroker
from time import sleep
import sys
import numpy as np
import matplotlib.pyplot as plt
from pam import rate_map, auditory_nerve, cross_correlation, normalise
from audioreceiver import AudioReceiver

def main():

	NAO_IP = "169.254.103.126"  # "169.254.88.3"
	NAO_PORT = 9559
	CHANNELS = 32 # number of frequency channels
	BUFFER_SIZE = 4096 # this is the size of the audio buffer used by naoqi
	MAX_DELAY = 24 # this is a guess, but its too big!!!!
	
	# we need a broker object to handle subscription of one module to another
	# and it needs to stay in memory all the time the program is running
	
	myBroker = ALBroker("myBroker","0.0.0.0",0,NAO_IP,NAO_PORT) 

	# start the audio receiver going

	global myAudio
	# zero means all channels, 48kHz
	myAudio = AudioReceiver("myAudio",NAO_IP,NAO_PORT,0)
	myAudio.start()
	
	# figure
		
	fig,ax = plt.subplots(2,1)
	h1 = ax[0].imshow(np.random.rand(CHANNELS,BUFFER_SIZE),vmin=0.0,vmax=13.0,origin='lower',aspect='auto')
	h2 = ax[1].imshow(np.random.rand(CHANNELS,BUFFER_SIZE),vmin=0.0,vmax=13.0,origin='lower',aspect='auto')
	ax[0].set_title("Left Ear Energy")
	ax[1].set_title("Right Ear Energy")
	
	plt.tight_layout()
	plt.show(block=False)


	# mainloop
	
	try:
		lowerF = 100 
		upperF = 5000
		freqRange = (upperF-lowerF)/CHANNELS
		ilds = []
		itds = []
		ilds2 = []
		itds2 = []

		fig2, ax2 = plt.subplots(5,1)
		plt.xlabel("ILD")
		plt.ylabel("ITD")
		#ax2[0].set_title("ILD vs ITD for ch 20")#+ lowerF+(3*freqRange)+ "-"+ lowerF+((3+1)*freqRange)+"Hz")
		#ax2[1].set_title("ILD vs ITD for ch 30")#+ lowerF+(16*freqRange)+ "-"+ lowerF+((16+1)*freqRange)+"Hz")

		xedges = range(-40,40)
		yedges = range(-25,25)

		while True:
			sleep(0.1)
			left_sig = myAudio.soundData[2,:]
			left_an = auditory_nerve(left_sig,lowerF,upperF,CHANNELS,48000)
			h1.set_data(left_an)
			right_sig = myAudio.soundData[3,:]
			right_an = auditory_nerve(right_sig,lowerF,upperF,CHANNELS,48000)
			h2.set_data(right_an)
			plt.draw()
			# the filters take some time to start up, so suggest that you use the
			# last half of this data to compute the cross-correlation function in
			# each channel
			# You won't need as many as 128 channels - 32 would be good
			# compute the ILD in one band
			print "---------------------------------------------"

			for chan in range(0,CHANNELS):
				x = left_an[chan,2048:BUFFER_SIZE-1]
				y = right_an[chan,2048:BUFFER_SIZE-1]
				left_energy = np.sum(np.square(x))
				right_energy = np.sum(np.square(y))
				# compute the itd
				ccg = cross_correlation(x,y,MAX_DELAY)
				ccg = normalise(ccg) # check this - is it needed?
				itd = np.argmax(ccg)-MAX_DELAY
				ild = 10.0*np.log10(left_energy/right_energy)
				print "channel",chan, "freq range: ", lowerF+(chan*freqRange), "-", lowerF+((chan+1)*freqRange), "Hz, ILD:", ild, "ITD:", itd

				if (chan==27):
					ilds.append(ild)
					itds.append(itd)
					H, xedges, yedges = np.histogram2d(itds, ilds, bins=(xedges, yedges))
					im = ax2[0].imshow(H, interpolation='nearest', origin='low', aspect='auto', extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])

				elif (chan==28):
					ilds2.append(ild)
					itds2.append(itd)
					H, xedges, yedges = np.histogram2d(itds2, ilds2, bins=(xedges, yedges))
					im = ax2[1].imshow(H, interpolation='nearest', origin='low', aspect='auto', extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
			
			print "---------------------------------------------"		
			# prevents figure from freezing on Windows
			plt.pause(0.00001)

						
	except KeyboardInterrupt:
		print "Interrupted by user, shutting down"
		myBroker.shutdown()
		sleep(2)
		sys.exit(0)

# run it

if __name__ == "__main__":
    main()
