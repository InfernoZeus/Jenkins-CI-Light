import socket
import time
import pygame
import sys

UDP_IP = "192.168.1.15" #this is the IP of the wifi bridge
UDP_PORT = 50000

TURN_LIGHT_OFF = "\x21\x00\x55" #this turns all lights off
TURN_LIGHT_ON = "\x22\x00\x55"
MODE_DOWN = "\x28\x00\x55"
MODE_UP = "\x27\x00\x55"
GREEN = "\x20\x70\x55"
RED = "\x20\xB0\x55"

def demo(sock):
	# Green Light
	sock.sendto(GREEN, (UDP_IP, UDP_PORT))
	time.sleep(5)

	# Play sound
	pygame.init()
	sound = pygame.mixer.Sound('sound.wav')
	sound.set_volume(1.0)
	sound.play()
	time.sleep(2)
	# Switch to 'Mode' mode - should be set to flashing red manually first
	sock.sendto(MODE_DOWN, (UDP_IP, UDP_PORT))
	time.sleep(5)

	# Stop sound
	sound.stop()

	# Switch back to Green
	sock.sendto(GREEN, (UDP_IP, UDP_PORT))
	time.sleep(0.3)

def success_mode(sock):
	sock.sendto(GREEN, (UDP_IP, UDP_PORT))

def fail_mode(sock):
	# Play sound
	pygame.init()
	sound = pygame.mixer.Sound('sound.wav')
	sound.set_volume(1.0)
	sound.play()
	time.sleep(2)
	sock.sendto(GREEN, (UDP_IP, UDP_PORT))
	time.sleep(0.05)
	# Switch to 'Mode' mode - should be set to flashing red manually first
	sock.sendto(MODE_DOWN, (UDP_IP, UDP_PORT))
	time.sleep(sound.get_length())

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(TURN_LIGHT_ON, (UDP_IP, UDP_PORT))
time.sleep(0.1)

arg_len = len(sys.argv)
if (arg_len == 1):
	demo(sock)
elif (arg_len == 2):
	success = sys.argv[1]
	print "arg", sys.argv[1]
	if (success == "1"):
		success_mode(sock)
	elif (success == "0"):
		fail_mode(sock)
	else:
		print "Error: argument for success/failure should either be 1 for success or 0 for failure"
else:
	print "Error: 1 argument should be passed indicating success or failure (1/0), or no arguments for demo mode"
	print "Args: ", str(sys.argv)







