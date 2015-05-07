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
    
  fig, (ax1,ax2) = plt.subplots(1,2, sharey=True)
  ax1.set_title("Left Ear")
  #h1 = ax1.imshow(np.random.rand(341,500),vmin=0.0,vmax=70.0,origin='lower')
  ax2.set_title("Right Ear")
  #ax3.set_title("XCorr")
  #h2 = ax2.imshow(np.random.rand(341,500),vmin=0.0,vmax=70.0,origin='lower')
  plt.show(block=False)


  # we need a broker object to handle subscription of one module to another
  # and it needs to stay in memory all the time the program is running
  # without this, the audioreceiver won't properly subscribe to the audio service
  
  #uncomment
  myBroker = ALBroker("myBroker","0.0.0.0",0,NAO_IP,NAO_PORT) 

  # start the audio receiver going

  global leftEar
  leftEar = AudioReceiver("leftEar",NAO_IP,NAO_PORT)
  leftEar.start(1)

  global rightEar
  rightEar = AudioReceiver("rightEar",NAO_IP,NAO_PORT)
  rightEar.start(2)

  # only stop if on ctrl-c
  
  try:
    # max 2500 samples in the arrays
    energySamplesL = []
    energySamplesR = []
    # x is time domain
    x = []
    time = 0;
    while True:
      sleep(0.01)
      
      #h1.set_data(leftEar.specgram)
      #h2.set_data(rightEar.specgram)
      energyL = leftEar.computeEnergy(1)
      energyR = rightEar.computeEnergy(2)

      if len(energySamplesL) > 2500:
        x.pop(0)
        energySamplesL.pop(0)
        energySamplesR.pop(0)
      
      x.append(time)
      energySamplesL.append(energyL)
      energySamplesR.append(energyR)

      # Square each value in the samples array and sum them
      sigmaSquaredL = square(energySamplesL)
      sigmaSquaredR = square(energySamplesR)

      ild = 10 * np.log10(sum(sigmaSquaredL)/sum(sigmaSquaredR))

      # 

      time += 0.01
      ax1.plot(x, energySamplesL)
      ax2.plot(x, energySamplesR)
      print "ILD: ", ild
      print "ITD: ", np.correlate(energySamplesL, energySamplesR)
      
      #energyL = 2000#
      #energyR = 1000#
      
      plt.draw()
      # if energy > 2000:
      #   print "Left Ear Energy: ", leftEar.computeEnergy(1)

  except KeyboardInterrupt:
    print "Interrupted by user, shutting down"
    #myBroker.shutdown()
    sys.exit(0)

def square(ls):
  return [i ** 2 for i in ls]

if __name__ == "__main__":
    main()

