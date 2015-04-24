# Written by Ann Nee Lau and Laura Craciun

from naoqi import ALProxy, ALModule, ALBroker
from time import sleep
import sys
import matplotlib.pyplot as plt
from pam import rate_map, auditory_nerve, cross_correlation, normalise
from audioreceiver import AudioReceiver
import almath
import glob
import scipy
import numpy as np
from sklearn import mixture
import sys, getopt, re
import math

class CommandLine:
	def __init__(self):
		constants = Constants()
		
		try:
			opts, args = getopt.getopt(sys.argv[1:],"hcl", ["help", "collect data", "localize sound"])

		except getopt.GetoptError:
			print 'An error has occurred. Type -h or --help to get help'
			sys.exit(2)

		if len(opts) == 0:
			print "type -h or --help to get help"
			sys.exit(2)	

		for opt, arg in opts:
			if opt in ("-h", "--help"):
				print 'Options for running this script:'
				print '-c or --collect data to collect training data'
				print '-l or --localize sound to run the sound localization algorithm'
			
			elif opt in ("-c", "--collect data"):
				TrainingData(constants).collectTrainingData()

			elif opt in ("-l", "--localize sound"):
				processedData = ProcessData()
				SoundLocalizer(constants, processedData).localizeSound()


# A class that declares constants shared across multiple classes
class Constants:
	def __init__(self):
		self.NAO_IP = "169.254.88.3" #"169.254.103.126" 
		self.NAO_PORT = 9559
		self.CHANNELS = 32  	# number of channels
		self.BUFFER_SIZE = 4096 # this is the size of the audio buffer used by naoqi
		self.MAX_DELAY = 24 
		self.MAX_MOTOR_SPEED = 0.2
		self.LOWER_FREQ = 100
		self.UPPER_FREQ = 5000

# Collects training data to be used in the sound localization module
class TrainingData:
	def __init__(self, constants):
		self.constants = constants
		# how many ITDs and ILDs we want to collect for training 
		self.NUM_MEASUREMENTS = 200 # number of ITD's and ILD's to collect for each azimuth
		self.CHANNEL = 22			# the channel we want to extract data from
		self.AZIMUTH_DELTA = 10		# how much to increment by

	def collectTrainingData(self):
		# we need a broker object to handle subscription of one module to another
		# and it needs to stay in memory all the time the program is running	
		myBroker = ALBroker("myBroker","0.0.0.0",0,self.constants.NAO_IP,self.constants.NAO_PORT) 

		# prepare robot for head movement
		motion = ALProxy("ALMotion",self.constants.NAO_IP,self.constants.NAO_PORT)
		motion.setStiffnesses(["HeadYaw","HeadPitch"],[1.0,1.0])

		# prepare robot for speech
		speechProxy = ALProxy("ALTextToSpeech",self.constants.NAO_IP,self.constants.NAO_PORT)

		# start the audio receiver going
		global myAudio
		# zero means all channels, 48kHz
		myAudio = AudioReceiver("myAudio",self.constants.NAO_IP,self.constants.NAO_PORT,0)
		myAudio.start()
		
		try:
			azimuth = range(50,91, self.AZIMUTH_DELTA)
			
			for angle in azimuth:
				speechProxy.say("Recording measurements at " + str(angle) + " degrees")
				# format: [ [itd1,ild1], [itd2,ild2], etc... ]
				data = []
				motion.setAngles("HeadYaw",[angle*almath.TO_RAD],self.constants.MAX_MOTOR_SPEED)

				while len(data) < self.NUM_MEASUREMENTS:
					sleep(0.1)

					left_sig = myAudio.soundData[2,:]
					left_an = auditory_nerve(left_sig,self.constants.LOWER_FREQ,self.constants.UPPER_FREQ,self.constants.CHANNELS,48000)
					
					right_sig = myAudio.soundData[3,:]
					right_an = auditory_nerve(right_sig,self.constants.LOWER_FREQ,self.constants.UPPER_FREQ,self.constants.CHANNELS,48000)
				
					x = left_an[self.CHANNEL,2048:self.constants.BUFFER_SIZE-1]
					y = right_an[self.CHANNEL,2048:self.constants.BUFFER_SIZE-1]

					# compute ILD
					left_energy = np.sum(np.square(x))
					right_energy = np.sum(np.square(y))
					ild = 10.0*np.log10(left_energy/right_energy)

					# compute ITD
					ccg = cross_correlation(x,y,self.constants.MAX_DELAY)
					ccg = normalise(ccg)
					itd = np.argmax(ccg)-self.constants.MAX_DELAY

					data.append([itd,ild])
					
				# save array to file
				filename = repr(angle) + '_ITDS_ILDS.txt'

				# save itds and ilds in a text file
				np.savetxt(filename, np.array(data))

			speechProxy.say("Finished!")
			myBroker.shutdown()
			sleep(2)
			sys.exit(0)

		except KeyboardInterrupt:
			print "Interrupted by user, shutting down"
			myBroker.shutdown()
			sleep(2)
			sys.exit(0)

# Processes training data to be used in the sound localization module
class ProcessData:
	def __init__(self):
		# Get all the raw data files containing ITDs and ILDs
		raw_data_files =  glob.glob("*.txt")

		# Each key (azimuth) will be matched to a GMM object
		self.gmms = dict()

		# Fit the ITD's and ILD's into a GMM for each azimuth and store it in a dictionary
		for data_file in raw_data_files:
			data = np.loadtxt(data_file)
			azimuth = data_file.split("_")[0]
			gmm = mixture.GMM(n_components=1)
			gmm.fit(data)
			self.gmms[int(azimuth)] = gmm

		# for key in itds:
		# 	print np.round(itds[key].means_, 2)
		# 	print np.round(ilds[key].means_, 2)
		# 	print "-----"

# The sound localization module
class SoundLocalizer:
	def __init__(self, constants, processedData):
		self.constants = constants
		self.GMMS = processedData.gmms
		self.CHANNEL = 22 # the channel we want
		self.NUM_MEASUREMENTS = 5 

	def localizeSound(self):
		# we need a broker object to handle subscription of one module to another
		# and it needs to stay in memory all the time the program is running	
		myBroker = ALBroker("myBroker","0.0.0.0",0,self.constants.NAO_IP,self.constants.NAO_PORT) 

		# prepare robot for head movement
		motion = ALProxy("ALMotion",self.constants.NAO_IP,self.constants.NAO_PORT)
		motion.setStiffnesses(["HeadYaw","HeadPitch"],[1.0,1.0])

		# prepare robot for speech
		speechProxy = ALProxy("ALTextToSpeech",self.constants.NAO_IP,self.constants.NAO_PORT)

		# start the audio receiver going
		global myAudio
		# zero means all channels, 48kHz
		myAudio = AudioReceiver("myAudio",self.constants.NAO_IP,self.constants.NAO_PORT,0)
		myAudio.start()
		
		try:
			data = []
			sleep(1.0)
			while True:

				# collect enough ITDs and ILDs
				if len(data) < self.NUM_MEASUREMENTS:	
					sleep(0.1)
					
					left_sig = myAudio.soundData[2,:]
					left_an = auditory_nerve(left_sig,self.constants.LOWER_FREQ,self.constants.UPPER_FREQ,self.constants.CHANNELS,48000)
					
					right_sig = myAudio.soundData[3,:]
					right_an = auditory_nerve(right_sig,self.constants.LOWER_FREQ,self.constants.UPPER_FREQ,self.constants.CHANNELS,48000)
				
					x = left_an[self.CHANNEL,2048:self.constants.BUFFER_SIZE-1]
					y = right_an[self.CHANNEL,2048:self.constants.BUFFER_SIZE-1]

					# compute ILD
					left_energy = np.sum(np.square(x))
					right_energy = np.sum(np.square(y))
					ild = 10.0*np.log10(left_energy/right_energy)

					# compute ITD
					ccg = cross_correlation(x,y,self.constants.MAX_DELAY)
					ccg = normalise(ccg)
					itd = np.argmax(ccg)-self.constants.MAX_DELAY

					data.append([itd,ild])

				# compute log probability 
				else:

					# format: {azimuth: average probability}
					probabilities = dict()

					for azimuth in self.GMMS.keys():
						gmm = self.GMMS[azimuth]
						# convert each log probability to probability and sum it
						logProbs = gmm.score(data)
						prob = 0
						for x in logProbs:
							prob = prob + math.pow(math.e, x)

						# map azimuth to average probability and store it in a dictionary
						probabilities[azimuth] = prob/len(logProbs)

					# sort probability dictionary
					probabilities = sorted(probabilities.items(), key=lambda x: x[1], reverse=True) 
					# get angle with highest probability
					desiredAngle = probabilities[0][0]

					motion.setAngles("HeadYaw",[desiredAngle*almath.TO_RAD],self.constants.MAX_MOTOR_SPEED)
					speechProxy.say("Sound detected at " + str(desiredAngle) + " degrees")
					# reset arrays
					data = []
					myBroker.shutdown()
					sleep(2)
					sys.exit(0)

		except KeyboardInterrupt:
			print "Interrupted by user, shutting down"
			myBroker.shutdown()
			sleep(2)
			sys.exit(0)

if __name__ == '__main__':
	cmd = CommandLine()