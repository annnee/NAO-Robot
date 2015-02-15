from naoqi import ALProxy
import sys, getopt

def main(argv):

   # default parameters

   ip_address = "192.168.1.104"
   port = 9559
   string_to_say = ""
   
   try:
      opts, args = getopt.getopt(argv,"hs:i:p:")
   except getopt.GetoptError:
      print "say.py -s <string to say> -i <IP address> -p <port number>"
      sys.exit()
   for opt, arg in opts:
      if opt == "-h":
         print "say.py -s <string to say> -i <IP address> -p <port number>"
         sys.exit()
      elif opt == "-s":
         string_to_say = arg
      elif opt == "-i":
         ip_address = arg
      elif opt == "-p":
         port = int(arg)
   
   if string_to_say:    
      proxy = ALProxy("ALTextToSpeech",ip_address,port)
      proxy.say(string_to_say)
			
if __name__ == "__main__":
   main(sys.argv[1:])
	
	

