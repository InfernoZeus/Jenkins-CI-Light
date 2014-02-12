import json

class Control():
	commands = {}

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
		raise NotImplementedError("Please implement this method.")


class DemoControl(Control):
	def __init__(self, json):
		self.json = json

	def process(self, server):
		new_mode = self.json['mode']
		server.set_demo_mode(new_mode)
Control.register("demo", DemoControl)

