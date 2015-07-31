import argparse
import socket
from select import select
import logging
import logging.config
import os
import json
import sys

from accelleran import Job, Status, Cache, Alarm, Control
import limitlessled



class Server:

	def __init__(self):
		parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
		parser.add_argument("-q", "--quiet", help="Disable alarm sounds", action="store_true", default=False)
		parser.add_argument("-v", "--verbose", help="Enable extra verbose logging", action="store_true", default=False)
		parser.add_argument("--enable-console", help="Enable console logging", action="store_true", default=False)
		parser.add_argument("--listen-port", help="Port to listen for notifications from Jenkins", type=_port, default=50000)
		parser.add_argument("--listen-host", help="Host to listen for notifications from Jenkins", type=_host, default="0.0.0.0")
		parser.add_argument("--bridge-port", help="Port to send messages to the LimitlessLed Wifi Bridge", type=_port, default=50000)

		parser.add_argument("bridge_host", metavar="bridge-host", help="Hostname or IP address of the LimitlessLed Wifi Bridge", type=_host)
		self._args = parser.parse_args()
		self._cache = Cache()
		self._alarm = None
		self.demo_mode = False

		self.setup_logging()
		self.logger = logging.getLogger(self.__class__.__name__)

		self._light = self.connect_to_light(self._args.bridge_host, self._args.bridge_port)
		self.set_light_red(True)
		self.set_light_green()

	def setup_logging(self, default_path="logging.json", default_level=logging.INFO, env_key="LOG_CFG"):
		path = os.getenv(env_key, default_path)
		path = os.path.join(os.path.dirname(__file__), path)
		if os.path.exists(path):
			with open(path, 'rt') as f:
				config = json.load(f)
			logging.config.dictConfig(config)
		else:
			logging.basicConfig(level=default_level)

		if self._args.verbose:
			rootLogger = logging.getLogger()
			rootLogger.setLevel(logging.DEBUG)

		if not self._args.enable_console:
			rootLogger = logging.getLogger()
			for handler in rootLogger.handlers:
				if handler.__class__ == logging.StreamHandler:
					rootLogger.removeHandler(handler)

	def connect_to_light(self, bridge_ip, bridge_port):
		rgb = limitlessled.connect(bridge_ip, bridge_port, short_pause_duration=0.1, long_pause_duration=0.3).rgb
		return rgb

	def run(self):

		self._listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._listen_sock.bind((self._args.listen_host, self._args.listen_port))

		try:
			stop = False
			while not stop:
				try:
					data = self.read_data_from_socket()
					self.logger.debug(data)
					try:
						new_job = Job.fromJson(data)
						self.logger.info(new_job)
						self.process_job(new_job)
					except TypeError as e:
						try:
							# Check if JSON is control message
							control = Control.fromJson(data)
							control.process(self)
						except TypeError as e1:
							self.logger.warn(e)
							self.logger.warn(e1)
				except IOError:
					self.logger.exception("Unexpected error:")
				except (KeyboardInterrupt, SystemExit):
					stop = True
				except:
					self.logger.exception("Unexpected error:")
		finally:
			self._listen_sock.close()

	def read_data_from_socket(self):
		readable, _, _ = select([self._listen_sock], [], [])
		for sock in readable:
			data = sock.recv(1024)
			if data:
				return data
			else:
				raise IOError

	def process_job(self, new_job):
		if new_job.status == Status.NotFinished:
			return

		if self.demo_mode:
			if new_job.cache and new_job.status == Status.Failed:
				self._cache.add_job(new_job)
			else:
				self._cache.remove_job(new_job)
		else:
			if new_job.cache and new_job.status == Status.Failed:
				self._cache.add_job(new_job)
				self.update_light_from_cache()
			else:
				self._cache.remove_job(new_job)
				if new_job.status == Status.Failed:
					self.stop_alarm()
					self.start_alarm()
					self.set_light_red()
				else:
					self.update_light_from_cache()

	def update_light_from_cache(self):
		if self._cache.is_empty():
			self.stop_alarm()
			self.set_light_green()
		else:
			self.logger.info("Cached failing jobs: %s", self._cache)
			self.start_alarm()
			self.set_light_red()

	def start_alarm(self):
		if self._args.quiet:
			return
		if self._alarm is None:
			self.logger.debug("Starting alarm noise")
			self._alarm = Alarm()
			self._alarm.start()

	def stop_alarm(self):
		if self._args.quiet:
			return
		if self._alarm is not None:
			self.logger.debug("Stopping alarm noise")
			self._alarm.stop()
			self._alarm.join()
			self._alarm = None

	def set_light_green(self):
		self._light.set_color(limitlessled.Colors.lime_green)

	def set_light_red(self, reset=False):
		if reset:
			self._light.set_mode(limitlessled.PartyModes.red_blink)
		else:
			self.set_light_green()
			self._light.mode_up()

def _port(port):
	"""
	Validates argparse port argument.
	Accepts a single port.
	"""

	valid_range = range(1, 65535 + 1)

	try:
		port = int(port)
		if port not in valid_range:
			raise argparse.ArgumentTypeError("Port must be 1-65535")
		return port
	except ValueError:
		raise argparse.ArgumentTypeError("Port must be 1-65535")

def _host(name):
	"""
	Validates argparse hostname argument.
	Accepts an ip address or a domain name.
	"""

	try:
		socket.gethostbyname(name)
		return name
	except socket.error:
		raise argparse.ArgumentTypeError("Invalid hostname: " + name)
	try:
		socket.inet_aton(name)
		return name
	except socket.error:
		raise argparse.ArgumentTypeError("Invalid ip address: " + name)

if __name__ == "__main__":
	server = Server()
	server.run()
