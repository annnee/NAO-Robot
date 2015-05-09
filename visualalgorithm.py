# -*- encoding: UTF-8 -*-
# Adapted by Ann Nee Lau
# Original code taken from http://doc.aldebaran.com/1-14/dev/python/examples/vision/get_image.html
# Get an image from NAO andfilter out all colors but red and display filtered image

import matplotlib.pyplot as plt
import sys
import time
import numpy as np
import Image                    # Python Image Library
from naoqi import ALProxy


def showNaoImage(IP, PORT):
  camProxy = ALProxy("ALVideoDevice", IP, PORT)
  resolution = 2    # VGA
  colorSpace = 11   # RGB

  videoClient = camProxy.subscribe("python_client", resolution, colorSpace, 5)

  t0 = time.time()

  # Get a camera image.
  # image[6] contains the image data passed as an array of ASCII chars.
  naoImage = camProxy.getImageRemote(videoClient)

  camProxy.unsubscribe(videoClient)

  """
  Now we work with the image returned and save it as a PNG  using ImageDraw
  package.
  """
  # Get the image size and pixel array.
  imageWidth = naoImage[0]
  imageHeight = naoImage[1]
  array = naoImage[6]

  # Create a PIL Image from our pixel array.
  im = Image.fromstring("RGB", (imageWidth, imageHeight), array)

  # Save the image.
  im.save("camImage.png", "PNG")
  I = np.asarray(Image.open('camImage.png'), dtype='int64')
  newImg = np.copy(I)

  for x in range(0,imageHeight):
    for y in range(0,imageWidth):
      R = newImg[x,y][0] 
      G = newImg[x,y][1] 
      B = newImg[x,y][2]

      # If not red, make it black
      if R < G or R < B:
        newImg[x,y][0] = 0
        newImg[x,y][1] = 0
        newImg[x,y][2] = 0
      
      # Filter out white/grey 
      elif G> 50 or B > 50:
        newImg[x,y][0] = 0
        newImg[x,y][1] = 0
        newImg[x,y][2] = 0

  fig, ax = plt.subplots(1,2)

  ax[0].set_title("Original Image")
  ax[0].imshow(np.uint8(I))
  
  ax[1].set_title("Red Filtered Image")
  ax[1].imshow(np.uint8(newImg))
  
  plt.show()

  # An attempt at locating red objects in the processed image, remains incomplete.
  # redCountCol = []
  # redCountRow = []
  # fig,ax = plt.subplots(2,1)
  # fig.tight_layout()
  # plt.show(block=False)

  # for x in range(0,imageHeight):
  #   redCount = 0
  #   for y in range(0,imageWidth):
  #     if newImg[x,y][0]:
  #       redCount += 1   
  #   redCountCol.append(redCount)

  # for y in range(0,imageWidth):
  #   redCount = 0
  #   for x in range(0,imageHeight):
  #     if newImg[x,y][0]:
  #       redCount += 1
  #   redCountRow.append(redCount)

  # ax[0].set_title("COL")
  # ax[1].set_title("ROW")
  # ax[0].plot(range(0,480), redCountCol)
  # ax[1].plot(redCountRow, range(0,640))
  # plt.draw()
  # print redCountCol
  # print len(redCountCol)

  
NAO_IP = "169.254.88.3" #"169.254.103.126" 
NAO_PORT = 9559
showNaoImage(NAO_IP, NAO_PORT)