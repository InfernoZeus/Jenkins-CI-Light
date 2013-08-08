import socket
import time
import pygame
import sys

UDP_IP = "192.168.1.15" #this is the IP of the wifi bridge
UDP_PORT = 50000

TURN_LIGHT_OFF = "\x21\x00\x55" #this turns all lights off
TURN_LIGHT_ON = "\x22\x00\x55"
BRIGHT_UP = "\x23\x00\x55"
BRIGHT_DOWN = "\x24\x00\x55"
MODE_DOWN = "\x28\x00\x55"
MODE_UP = "\x27\x00\x55"
GREEN = "\x20\x70\x55"
RED = "\x20\xB0\x55"

def send(sock, msg, sleep=0.5):
	sock.sendto(msg, (UDP_IP, UDP_PORT))
	time.sleep(sleep)

def demo(sock):
	# Green Light
	success_mode(sock)
	time.sleep(5)

	# Play sound
	fail_mode(sock, 5)

	# Switch back to Green
	success_mode(sock)

def success_mode(sock):
	send(sock, GREEN)
	for i in range(9):
		send(sock, BRIGHT_DOWN)

def fail_mode(sock, sleep=0):
	# Play sound
	pygame.init()
	sound = pygame.mixer.Sound('sound.wav')
	sound.set_volume(1.0)
	sound.play()
	time.sleep(2)
	send(sock, GREEN)
	# Switch to 'Mode' mode - should be set to flashing red manually first
	send(sock, MODE_DOWN)
	for i in range(9):
		send(sock, BRIGHT_UP)
	if (sleep > 0):
		time.sleep(sleep)
		sound.stop()
	else:
		time.sleep(sound.get_length())
		sound.stop()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send(sock, TURN_LIGHT_ON)

arg_len = len(sys.argv)
if (arg_len == 1):
	demo(sock)
elif (arg_len == 2):
	success = sys.argv[1]
	if (success == "1"):
		success_mode(sock)
	elif (success == "0"):
		fail_mode(sock)
	else:
		print "Error: argument for success/failure should either be 1 for success or 0 for failure"
else:
	print "Error: 1 argument should be passed indicating success or failure (1/0), or no arguments for demo mode"
	print "Args: ", str(sys.argv)







