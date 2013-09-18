#!/usr/bin/env python

import socket
import time
import pygame
import sys
import json
import getopt
import logging
import threading
import os
import signal

SEND_UDP_IP = "192.168.1.15" #this is the IP of the wifi bridge
SEND_UDP_PORT = 50000

LISTEN_UDP_IP = "0.0.0.0"
LISTEN_UDP_PORT = 50000

COMMANDS = {
'TURN_LIGHT_OFF' : "\x21\x00\x55",
'TURN_LIGHT_ON' : "\x22\x00\x55",
'BRIGHT_UP' : "\x23\x00\x55",
'BRIGHT_DOWN' : "\x24\x00\x55",
'SPEED_UP' : "\x25\x00\x55",
'SPEED_DOWN' : "\x26\x00\x55",
'MODE_UP' : "\x27\x00\x55",
'MODE_DOWN' : "\x28\x00\x55",
'GREEN' : "\x20\x70\x55",
'RED' : "\x20\xB0\x55"
}

COMMAND_LOOKUP = dict((v,k) for k,v in COMMANDS.iteritems())

QUIET = False
MODE = ""
FAIL_THREAD = None

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s | %(levelname)7s | %(message)s"
# Only used in Server mode
CONSOLE_LOGGING = False

FAILING_JOBS = set()

def send(sock, msg, sleep=0.3):
	logger.debug("Sent %s to LED" % COMMAND_LOOKUP[msg])
	sock.sendto(msg, (SEND_UDP_IP, SEND_UDP_PORT))
	time.sleep(sleep)

def demo(sock):
	# Green Light
	success_mode(sock)
	time.sleep(5)

	# Show fail mode
	thread = fail_mode_thread(sock, 10)
	thread.start()

	# Switch back to Green
	success_mode(sock)

def success_mode(sock):
	send(sock, COMMANDS['GREEN'])
	for i in range(9):
		send(sock, COMMANDS['BRIGHT_DOWN'], 0.1)

class fail_mode_thread (threading.Thread):
	def __init__(self, sock, sleep=0):
		threading.Thread.__init__(self)
		self.sock = sock
		self.sleep = sleep
		self._stop = threading.Event()

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	def run(self):
		# Play sound
		if not QUIET:
			pygame.init()
			sound_path = os.path.join(os.path.dirname(__file__), 'sound.wav')
			self.sound = pygame.mixer.Sound(sound_path)
			self.sound.set_volume(1.0)
			self.sound.play()
			time.sleep(2)
		send(self.sock, COMMANDS['GREEN'])
		# Switch to 'Mode' mode - should be set to flashing red manually first
		send(self.sock, COMMANDS['MODE_DOWN'])
		for i in range(9):
			send(self.sock, COMMANDS['BRIGHT_UP'], 0.05)
		if (self.sleep == 0 and not QUIET):
			self.sleep = self.sound.get_length()
		while (self.sleep > 0):
			if (self.stopped()):
				break
			time.sleep(1)
			self.sleep -= 1
		if not QUIET:
			self.sound.stop()
			pygame.quit()
		logger.debug("Exiting fail_mode_thread")

def stop_fail_thread():
	global FAIL_THREAD
	if (FAIL_THREAD != None):
		FAIL_THREAD.stop()
		FAIL_THREAD.join()

def start_fail_thread(sock):
	global FAIL_THREAD
	if (FAIL_THREAD == None):
		FAIL_THREAD = fail_mode_thread(sock)
		FAIL_THREAD.start()

def call_corresponding_mode(sock, status, job=None):
	global FAIL_THREAD, FAILING_JOBS
	if (job == None):
		stop_fail_thread()
	if (job != None):
		if (status == "FAILURE" or status == "0"):
			if (job != "Test Build Failure"):
				FAILING_JOBS.add(job)
		else:
			FAILING_JOBS.discard(job)

		if not FAILING_JOBS:
			stop_fail_thread()
			status = "SUCCESS"
		else:
			# If new job is failing, restart fail_thread
			# otherwise leave it running as previous job is failing
			if (status == "FAILURE"):
				stop_fail_thread()
			status = "FAILURE"

			status_string = "Jobs "
			for job in FAILING_JOBS:
				status_string += "\"" + job +"\" "
			status_string += "still failing."
			logger.debug(status_string)

	if (status == "1" or status == "SUCCESS"):
		success_mode(sock)
	elif (status == "0" or status == "FAILURE"):
		start_fail_thread(sock)
	else:
		print "Status should either be 1/0 or SUCCESS/FAILURE"

def print_help(exit_code, exit=True):
	print 'usage: led.py [-q] [--log=LEVEL] status'
	print '       led.py [-q] [--log=LEVEL] [--console-logging] --server'
	print '       led.py [-q] [--log=LEVEL] --demo'
	if exit:
		sys.exit(exit_code)

def set_mode(new_mode):
	global MODE
	if MODE == "":
		MODE = new_mode
		return True
	else:
		return False

def parse_arguments():
	try:
		opts, args = getopt.getopt(sys.argv[1:],"qsdh",["quiet","server", "demo", "help", "log=", "console-logging"])
	except getopt.GetoptError:
		print_help(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print_help(0)
		elif opt in ("-q", "--quiet"):
			global QUIET
			QUIET = True
		elif opt in ("-s", "--server"):
			if not set_mode("SERVER"):
				print_help(1)
		elif opt in ("-d", "--demo"):
			if not set_mode("DEMO"):
				print_help(1)
		elif opt in ("--log"):
			numeric_level = getattr(logging, arg.upper(), None)
			if not isinstance(numeric_level, int):
			    raise ValueError('Invalid log level: %s' % arg)
			global LOG_LEVEL
			LOG_LEVEL = numeric_level
		elif opt in ("--console-logging"):
			global CONSOLE_LOGGING
			CONSOLE_LOGGING = True
	set_mode("DIRECT")
	return args

args = parse_arguments()

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

formatter = logging.Formatter(LOG_FORMAT)

if (MODE == "SERVER"):
	log_path = os.path.join(os.path.dirname(__file__), 'jenkins-ci-light.log')
	fh = logging.FileHandler(log_path)
	fh.setFormatter(formatter)
	logger.addHandler(fh)

if (MODE == "SERVER" and CONSOLE_LOGGING) or (MODE != "SERVER"):
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)

logger.debug("Set Log Level to " + logging.getLevelName(LOG_LEVEL))

send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send(send_sock, COMMANDS['TURN_LIGHT_ON'])

if MODE == "SERVER":

	pid = str(os.getpid())
	pidfile = "/tmp/jenkins-ci-light.pid"

	if os.path.isfile(pidfile):
		print "%s already exists, exiting" % pidfile
		sys.exit()
	else:
		file(pidfile, 'w').write(pid)

	def handle_exit(signal, frame):
		os.unlink(pidfile)
		print "Stopped jenkins-ci-light server"
		sys.exit(0)

	signal.signal(signal.SIGTERM, handle_exit)
	signal.signal(signal.SIGINT, handle_exit)

	listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	listen_sock.bind((LISTEN_UDP_IP, LISTEN_UDP_PORT))

	logger.info("Listening on port %d" % LISTEN_UDP_PORT)

	while True:
		data, addr = listen_sock.recvfrom(1024) # buffer size is 1024 bytes
		logger.debug("Received \"" + data + "\"")
		try:
			info = json.loads(data)
			build_info = info['build']
			if build_info['phase'] == "FINISHED":
				job = info['name']
				status = build_info['status']
				logger.info("Build %s finished with status %s", job, status)
				call_corresponding_mode(send_sock, status, job)
		except ValueError as e:
			logger.warning(e)
			if LOG_LEVEL > logging.DEBUG:
				logger.warning(data)
		except:
			e = sys.exc_info()[0]
			logger.error(e)
elif MODE == "DEMO":
	demo(send_sock)
elif MODE == "DIRECT":
	arg_len = len(args)
	if arg_len != 1:
		print_help(1)
	else:
		status = args[0]
		call_corresponding_mode(send_sock, status)








