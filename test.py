import numpy as np
from sklearn import mixture
import math
import glob
from naoqi import ALProxy, ALModule, ALBroker
import pickle
import matplotlib.pyplot as plt
import almath
from time import sleep
from audioreceiver import AudioReceiver

folder = "Skylar-250-Anechoic-White-Noise"
raw_data_files = glob.glob(folder+"/*.p")
#print raw_data_files

files = [3,8,9,13,18]
degree_sign= u'\N{DEGREE SIGN}'


for f in files:
	data = pickle.load(open(raw_data_files[f], "rb"))
	
	angle = raw_data_files[f].replace(folder+"\\", "").split("_")[0]
	
	channels = [9,18,25,31]
	fig,ax = plt.subplots(2,2, sharey=True,sharex=True)
	fig.suptitle("Angle " + angle + degree_sign, fontsize=16)
	fig.subplots_adjust(hspace=0, wspace=0)


	i = 0
	for chan in channels:
		chanData = data[chan]	
		xdata = []
		ydata = []
		for (x,y) in chanData:
			xdata.append(x)
			ydata.append(y)

		if i/2 == 0 and i%2 == 0:
			ax[i/2, i%2].set_ylabel("ILD")
		elif i/2 == 1 and i%2 == 0:
			ax[i/2, i%2].set_xlabel("ITD")
			ax[i/2, i%2].set_ylabel("ILD")
		else:
			ax[i/2, i%2].set_xlabel("ITD")

		ax[i/2, i%2].set_title("Channel " + str(chan+1))
		ax[i/2, i%2].scatter(xdata, ydata, marker='.', color='b')

		i+=1

plt.show()	


# "169.254.103.126"
# "169.254.88.3"
# NAO_IP = "169.254.103.126"
# NAO_PORT = 9559
# MAX_MOTOR_SPEED = 0.2

# myBroker = ALBroker("myBroker","0.0.0.0",0,NAO_IP,NAO_PORT) 
# motion = ALProxy("ALMotion",NAO_IP,NAO_PORT)
# myAudio = ALProxy("ALAudioDevice",NAO_IP,NAO_PORT)

# myAudio.setOutputVolume(70)

# testing purposes
# angle = -40

# motion.setStiffnesses(["HeadYaw","HeadPitch"],[1.0,1.0])
# motion.setAngles("HeadYaw",[(angle)*almath.TO_RAD],MAX_MOTOR_SPEED)