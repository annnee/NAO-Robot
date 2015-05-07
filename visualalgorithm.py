# -*- encoding: UTF-8 -*-
# Adapted by Ann Nee Lau
# Get an image from NAO. Display it and save it using PIL.

import sys
import time
import numpy as np
# Python Image Library
import Image
import matplotlib.pyplot as plt

from naoqi import ALProxy


def showNaoImage(IP, PORT):
  """
  First get an image from Nao, then show it on the screen with PIL.
  """

  # camProxy = ALProxy("ALVideoDevice", IP, PORT)
  # resolution = 2    # VGA
  # colorSpace = 11   # RGB

  # videoClient = camProxy.subscribe("python_client", resolution, colorSpace, 5)

  # t0 = time.time()

  # # Get a camera image.
  # # image[6] contains the image data passed as an array of ASCII chars.
  # naoImage = camProxy.getImageRemote(videoClient)

  # camProxy.unsubscribe(videoClient)

  # Now we work with the image returned and save it as a PNG  using ImageDraw
  # package.

  # Get the image size and pixel array.
  # imageWidth = naoImage[0]
  # imageHeight = naoImage[1]
  # array = naoImage[6]

  # # Create a PIL Image from our pixel array.
  # im = Image.fromstring("RGB", (imageWidth, imageHeight), array)

  # # Save the image.
  # im.save("camImage.png", "PNG")
  imageHeight = 480
  imageWidth = 640
  I = np.asarray(Image.open('camImage.png'))
  newImg = np.copy(I)

  # redCountCol = []
  # redCountRow = []
  # fig,ax = plt.subplots(2,1)
  # fig.tight_layout()
  # plt.show(block=False)

  for x in range(0,imageHeight):
    #redCount = 0
    for y in range(0,imageWidth):
      newImg[x,y][1] = 0
      newImg[x,y][2] = 0
      #print newImg[x,y] 
      #redCount += I[x,y][0]    
    #redCountCol.append(redCount)

  # for y in range(0,imageWidth):
  #   redCount = 0
  #   for x in range(0,imageHeight):
  #     redCount += I[x,y][0]    
  #   redCountRow.append(redCount)

  # ax[0].set_title("COL")
  # ax[1].set_title("ROW")
  # ax[0].plot(range(0,480), redCountCol)
  # ax[1].plot(redCountRow, range(0,640))
  # plt.draw()

  im = Image.fromarray(np.uint8(newImg))
  im.show()
  # print redCountCol
  # print len(redCountCol)

NAO_IP = "169.254.88.3" #"169.254.103.126" 
NAO_PORT = 9559
showNaoImage(NAO_IP, NAO_PORT)