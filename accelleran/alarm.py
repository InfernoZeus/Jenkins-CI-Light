import os
import threading
import logging
import pygame

logger = logging.getLogger(__name__)

class Alarm (threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self._stop = threading.Event()
		self._finished = False

		pygame.init()
		sound_path = os.path.join(os.path.dirname(__file__), 'sound.wav')
		self._sound = pygame.mixer.Sound(sound_path)
		self._sound.set_volume(1.0)

	def stop(self):
		self._stop.set()

	def is_stopped(self):
		return self._stop.isSet()

	def is_finished(self):
		return self._finished

	def run(self):
		self._sound.play()

		timer = 0
		while (timer < self._sound.get_length()):
			if (self.is_stopped()):
				break
			time.sleep(1)
			timer += 1

		self._sound.stop()
		pygame.quit()
		self._finished = True
