import sys
import logging

logger = logging.getLogger(__name__)

class Cache:
	def __init__(self):
		self._cache = dict()

	def add_job(self, job):
		try:
			self._cache[job.get_id()] = job
		except AttributeError as e:
			raise TypeError("'job' object cannot be interpreted as a Job: " + str(e)), None, sys.exc_info()[2]

	def has_job(self, job):
		return job.get_id() in self._cache

	def remove_job(self, job):
		try:
			if self.has_job(job):
				del self._cache[job.get_id()]
		except AttributeError as e:
			raise TypeError("'job' object cannot be interpreted as a Job: " + str(e)), None, sys.exc_info()[2]

	def is_empty(self):
		return not self.__bool__()

	def __bool__(self):
		return bool(self._cache)

	__nonzero__=__bool__
