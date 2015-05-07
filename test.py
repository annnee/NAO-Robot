import numpy as np
from sklearn import mixture
import math
import glob
from naoqi import ALProxy, ALModule, ALBroker
import pickle
import matplotlib.pyplot as plt
import almath
from time import sleep

# raw_data_files = glob.glob("Walter-250-White-Noise/*.p")
# #print raw_data_files

# onefile = raw_data_files[7]
# print onefile

# data = pickle.load(open(onefile, "rb"))
# 	#x = x.replace("Training-Data\\", "")

# channels = [2,14,20,30]
# fig,ax = plt.subplots(len(channels))
# i = 0
# for chan in channels:
# 	print chan
# 	chanData = data[chan]
	
# 	xdata = []
# 	ydata = []
# 	for (x,y) in chanData:
# 		xdata.append(x)
# 		ydata.append(y)

# 	ax[i].plot(xdata, ydata, 'ro')
# 	i+=1
# plt.tight_layout()
# plt.show()	

NAO_IP = "169.254.103.126"
NAO_PORT = 9559
MAX_MOTOR_SPEED = 0.2

myBroker = ALBroker("myBroker","0.0.0.0",0,NAO_IP,NAO_PORT) 
motion = ALProxy("ALMotion",NAO_IP,NAO_PORT)
#print 

# angle = motion.getAngles('HeadYaw',True)[0] * (180/math.pi)
# print angle

#motion.setAngles("HeadYaw",[(70)*almath.TO_RAD],0.2)
motion.setStiffnesses(["HeadYaw","HeadPitch"],[1.0,1.0])

motion.setAngles("HeadYaw",[(-60)*almath.TO_RAD],MAX_MOTOR_SPEED)
			

sleep(2)
