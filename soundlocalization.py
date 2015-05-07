# Written by Ann Nee Lau and Laura Craciun

from naoqi import ALProxy, ALModule, ALBroker
from time import sleep
from pam import rate_map, auditory_nerve, cross_correlation, normalise
from audioreceiver import AudioReceiver
import almath
import glob
import scipy
import numpy as np
from sklearn import mixture
import sys, getopt, re
import math
import pickle

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
				processedData = ProcessData(constants)
				SoundLocalizer(constants, processedData).localizeSound()


# A class that declares constants shared across multiple classes
class Constants:
	def __init__(self):
		# Walter - "169.254.103.126"
		# Skylar - "169.254.88.3"
		self.NAO_IP = "169.254.103.126"
		self.NAO_PORT = 9559
		self.CHANNELS = 32  	# number of channels
		self.BUFFER_SIZE = 4096 # this is the size of the audio buffer used by naoqi
		self.MAX_DELAY = 24 
		self.MAX_MOTOR_SPEED = 0.2
		self.LOWER_FREQ = 100
		self.UPPER_FREQ = 5000
		self.DATA_FOLDER = "Walter-250-Anechoic-White-Noise"# folder name containing training data

# Collects training data to be used in the sound localization module
class TrainingData:
	def __init__(self, constants):
		self.constants = constants
		# how many ITDs and ILDs we want to collect for training 
		self.NUM_MEASUREMENTS = 250 # number of ITD's and ILD's to collect for each azimuth
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
			azimuth = range(-90,91, self.AZIMUTH_DELTA)
			
			for angle in azimuth:

				# we need to rotate the head the opposite direction so that during sound localization, it turns its head in the right direction
				motion.setAngles("HeadYaw",[-angle*almath.TO_RAD],self.constants.MAX_MOTOR_SPEED)

				speechProxy.say("Recording measurements at " + str(angle) + " degrees")
				print "Recording measurements at " + str(angle) + " degrees"
				# format: {channel: [[itd1,ild1], [itd2,ild2],...], ... }
				# initalize dictionary
				data = {}
				data[0] = []
				# if we haven't collected the desired number of measurements for each channel for each location
				while len(data[0]) < self.NUM_MEASUREMENTS:
					sleep(0.1)

					left_sig = myAudio.soundData[2,:]
					left_an = auditory_nerve(left_sig,self.constants.LOWER_FREQ,self.constants.UPPER_FREQ,self.constants.CHANNELS,48000)
					
					right_sig = myAudio.soundData[3,:]
					right_an = auditory_nerve(right_sig,self.constants.LOWER_FREQ,self.constants.UPPER_FREQ,self.constants.CHANNELS,48000)
					
					for chan in range(0,self.constants.CHANNELS):
					
						x = left_an[chan,2048:self.constants.BUFFER_SIZE-1]
						y = right_an[chan,2048:self.constants.BUFFER_SIZE-1]

						# compute ILD
						left_energy = np.sum(np.square(x))
						right_energy = np.sum(np.square(y))

						ild = 0.0 if (left_energy == 0.0 or right_energy == 0.0) else (10.0*np.log10(left_energy/right_energy))

						# compute ITD
						ccg = cross_correlation(x,y,self.constants.MAX_DELAY)
						ccg = normalise(ccg)
						itd = np.argmax(ccg)-self.constants.MAX_DELAY

						if chan not in data:
							data[chan] = [[itd,ild]]
						else:
							ls = data[chan]
							ls.append([itd,ild])
							data[chan] = ls
					
				# save itds and ilds in a pickle file
				filename = repr(angle) + '_ITDS_ILDS.p'
				pickle.dump(data, open(self.constants.DATA_FOLDER+"/"+filename, "wb" ))

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
	def __init__(self, constants):
		# Get all the raw data files containing ITDs and ILDs
		raw_data_files =  glob.glob(constants.DATA_FOLDER+"/*.p")

		if len(raw_data_files) == 0:
			print "No training data found. Please collect training data before running this class"
			sys.exit(0)

		else:
			# Each key (azimuth) will be mapped to a dictionary in the form of {channel: gmm obj, channel2: gmm obj2, ...}
			self.gmms = dict()

			# Fit the ITD's and ILD's into a GMM for each channel for each azimuth and store it in a dictionary
			for data_file in raw_data_files:

				# Format = {channel: [[itd,ild],[itd2,ild2],...]}
				data = pickle.load(open(data_file, "rb"))
				data_file = data_file.replace(constants.DATA_FOLDER+"\\", "")
				azimuth = data_file.split("_")[0]
				self.gmms[int(azimuth)] = dict()

				for channel in data:
					itds_ilds = data[channel] 
					gmm = mixture.GMM(n_components=1)
					gmm.fit(itds_ilds)

					self.gmms[int(azimuth)][channel] = gmm

# The sound localization module
class SoundLocalizer:
	def __init__(self, constants, processedData):
		self.constants = constants
		self.GMMS = processedData.gmms
		self.NUM_MEASUREMENTS = 15 

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
			# format: {chan: [[itd,ild],...], chan2: [[itd2,ild2,...]], ...}
			data = dict()
			data[0] = []
			motion.setAngles("HeadYaw",[0],self.constants.MAX_MOTOR_SPEED)
			sleep(1)
			speechProxy.say("I am listening")
			while True:
				
				# collect enough ITDs and ILDs in each frequency channel
				if len(data[0]) < self.NUM_MEASUREMENTS:
					sleep(0.1)
					
					left_sig = myAudio.soundData[2,:]
					left_an = auditory_nerve(left_sig,self.constants.LOWER_FREQ,self.constants.UPPER_FREQ,self.constants.CHANNELS,48000)
					
					right_sig = myAudio.soundData[3,:]
					right_an = auditory_nerve(right_sig,self.constants.LOWER_FREQ,self.constants.UPPER_FREQ,self.constants.CHANNELS,48000)
					
					for chan in range(0,self.constants.CHANNELS):
						x = left_an[chan,2048:self.constants.BUFFER_SIZE-1]
						y = right_an[chan,2048:self.constants.BUFFER_SIZE-1]

						# compute ILD
						left_energy = np.sum(np.square(x))
						right_energy = np.sum(np.square(y))
						ild = 0.0 if (left_energy == 0.0 or right_energy == 0.0) else (10.0*np.log10(left_energy/right_energy))

						# compute ITD
						ccg = cross_correlation(x,y,self.constants.MAX_DELAY)
						ccg = normalise(ccg)
						itd = np.argmax(ccg)-self.constants.MAX_DELAY


						if chan not in data.keys():
							data[chan] = [[itd,ild]]
						else:
							ls = data[chan]
							ls.append([itd,ild])
							data[chan] = ls

				# compute log probability 
				else:

					# format: {azimuth: product of probabilities across 32 channels }
					probabilities = dict()

					for azimuth in self.GMMS:
						# grab all the gmms for an azimuth
						# each azimuth has 32 gmms - one gmm for each channel
						gmms = self.GMMS[azimuth]

						medianLogProbs = 0

						for channel in gmms:
							logprob = gmms[channel].score(data[channel])
							medianLogProbs += np.median(logprob)
						
						# convert the sum of the median log probabilities to probability
						# map azimuth to average probability and store it in a dictionary
						probabilities[azimuth] = math.pow(math.e, medianLogProbs)

					# sort probability dictionary
					probabilities = sorted(probabilities.items(), key=lambda x: x[1], reverse=True) 
					#print probabilities
					# get angle with highest probability
					desiredAngle = probabilities[0][0]

					motion.setAngles("HeadYaw",[(desiredAngle)*almath.TO_RAD],self.constants.MAX_MOTOR_SPEED)
					speechProxy.say("Sound detected at " + str(desiredAngle) + " degrees")
					print "Sound detected at " + str(desiredAngle) + " degrees"
					# reset dictionary
					data = dict()
					data[0] = []
					sleep(1)
					motion.setAngles("HeadYaw",[0],self.constants.MAX_MOTOR_SPEED)
					
					#myBroker.shutdown()
					sleep(2)
					speechProxy.say("I am listening")
					#sys.exit(0)

		except KeyboardInterrupt:
			print "Interrupted by user, shutting down"
			motion.setStiffnesses(["HeadYaw","HeadPitch"],[0.0,0.0])
			myBroker.shutdown()
			sleep(2)
			sys.exit(0)

if __name__ == '__main__':
	cmd = CommandLine()