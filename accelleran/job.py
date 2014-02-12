import json
import logging
import sys

logger = logging.getLogger(__name__)

class Status:
	NotFinished = "Not Finished"
	Succeeded = "Succeeded"
	Failed = "Failed"

class Job:

	def __init__(self, name, server, cache, status):
		self.name = name
		self.server = server
		self.cache = cache
		self.status = status

	def set_status(self, status):
		self.status = status

	def get_id(self):
		return self.name.replace(' ', '_') + "@" + self.server

	def __str__(self):
		cache_str = "caching" if self.cache else "not caching"
		return "Job " + self.name + " (" + cache_str + ") on " + self.server + ": " + self.status

	@classmethod
	def fromJson(cls, jsonString):
		try:
			info = json.loads(jsonString)
			name = info['name']
			server = info['server']
			cache = info['cache']
			build_info = info['build']
			phase = build_info["phase"]
			if phase != "FINISHED":
				status = Status.NotFinished
			else:
				status_string = build_info['status']
				if status_string == "SUCCESS":
					status = Status.Succeeded
				else:
					status = Status.Failed

			job = cls(name, server, cache, status)
			return job
		except KeyError as e:
			raise TypeError("Json does not represent a Job. Key missing: " + str(e)), None, sys.exc_info()[2]
