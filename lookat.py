from naoqi import ALProxy
import sys, getopt
import time
import almath

def main(argv):

   # default parameters

   ip_address = "192.168.1.100"
   port = 9559
   azimuth = 0.0
   elevation = 0.0
   given_elevation = False
   
   try:
      opts, args = getopt.getopt(argv,"ha:e:i:p:")
   except getopt.GetoptError:
      print "lookat.py -a <azimuth in [-90,90]> -e <elevation in [-25,20]> -i <IP address> -p <port number>"
      sys.exit()
   for opt, arg in opts:
      if opt == "-h":
         print "lookat.py -a <azimuth in [-90,90]> -e <elevation in [-25,20]> -i <IP address> -p <port number>"
         sys.exit()
      elif opt == "-a":
         azimuth = float(arg)
      elif opt == "-e":
         elevation = float(arg)
         given_elevation = True
      elif opt == "-i":
         ip_address = arg
      elif opt == "-p":
         port = int(arg)
   
   # stiffen motor and turn the head
   
   if azimuth>=-90 and azimuth<=90:
      proxy = ALProxy("ALMotion",ip_address,port)
      proxy.setStiffnesses("Head",1.0)
      if given_elevation:
         proxy.setAngles(["HeadYaw","HeadPitch"],[azimuth*almath.TO_RAD,elevation*almath.TO_RAD],0.2)
      else:
         proxy.setAngles("HeadYaw",[azimuth*almath.TO_RAD],0.2)
      time.sleep(3.0)
      proxy.setStiffnesses("Head",0.0)
			
if __name__ == "__main__":
   main(sys.argv[1:])
	
	

