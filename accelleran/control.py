import json
import logging

class Control():
	commands = {}
	logger = logging.getLogger(__name__)

	@staticmethod
	def register(command, clz):
		Control.commands[command] = clz

	@staticmethod
	def fromJson(jsonString):
		try:
			info = json.loads(jsonString)
			if 'command' in info:
				command = info['command']
				if command in Control.commands:
					clz = Control.commands[command]
					return clz(info)
		except KeyError as e:
			raise TypeError("Json does not represent a Control command. Key missing: " + str(e)), None, sys.exc_info()[2]

	def __init__(self, json):
		raise NotImplementedError("Override the constructor. Control objects shouldn't be created directly")

	def process(self, server):
		raise NotImplementedError("Implement this method.")


class DemoControl(Control):
	def __init__(self, json):
		self.json = json

	def process(self, server):
		action = self.json['action']
		if action == "enable_demo":
			self.logger.info("Enabling Demo Mode")
			server.demo_mode = True
			server.stop_alarm()
			server.set_light_green()
		elif action == "disable_demo":
			self.logger.info("Disabling Demo Mode")
			server.demo_mode = False
			server.update_light_from_cache()
		elif action == "start_alarm":
			self.logger.info("Starting Demo Alarm")
			server.start_alarm()
			server.set_light_red()
		elif action == "stop_alarm":
			self.logger.info("Stopping Demo Alarm")
			server.stop_alarm()
			server.set_light_green()

Control.register("demo", DemoControl)

class CacheControl(Control):
	def __init__(self, json):
		pass

	def process(self, server):
		server._cache.clear()
		server.update_light_from_cache()
		self.logger.info("Cleared failing job cache")
Control.register("clear", CacheControl)
