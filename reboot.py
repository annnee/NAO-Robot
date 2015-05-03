# reboot

from naoqi import ALProxy

NAO_IP = "169.254.88.3" #"169.254.103.126" 
NAO_PORT = 9559

proxy = ALProxy("ALSystem",NAO_IP,NAO_PORT)
proxy.reboot()


