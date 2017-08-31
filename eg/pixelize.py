# Spirale i,j
from __future__ import division
import math 
import random

# Pixelize around a random zone
	
def pixelize(img_jpg, colors):	
	W = int(math.sqrt(len(img_jpg)))
	L = W
	percents = [0, 0, 0]
	
	# Center zone:
	cx = random.uniform(0,L)
	cy = random.uniform(0,W)
	print("Cx = "+str(cx)+" , Cy = "+str(cy))

	thres = 0.2
	
	i = 0
	j = 0
	count = 0
	while i < W:
		j = 0
		while j < L:
			k = math.sqrt((i - cx)*(i - cx) + (j - cy)*(j - cy))/(W/1.5)
			if random.random() < thres*(1 - k) and img_jpg[j + i*L] == colors[0]:
				img_jpg[j + i*L] = colors[1]
			j += 1
		i += 1
		
	# Compensate bias
		cx = random.uniform(0,L)
	cy = random.uniform(0,W)
	print("Cx = "+str(cx)+" , Cy = "+str(cy))

	thres = 0.3
	
	i = 0
	j = 0
	count = 0
	while i < W:
		j = 0
		while j < L:
			k = math.sqrt((i - cx)*(i - cx) + (j - cy)*(j - cy))/(W/1.5)
			if random.random() < thres*(1 - k) and img_jpg[j + i*L] != colors[0]:
				img_jpg[j + i*L] = colors[0]
			j += 1
		i += 1
		
	
	# Recount value of percents
	i = 0
	j = 0
	while i < W:
		j = 0
		while j < L:
			if img_jpg[j + i*L] == colors[0]:
				percents[0] += 1
			elif img_jpg[j + i*L] == colors[1]:
				percents[1] += 1
			else:
				percents[2] += 1
			j += 1
		i += 1	 
	percents[0] = round(100*percents[0]/(W*L),1)
	percents[1] = round(100*percents[1]/(W*L),1)
	percents[2] = round(100*percents[2]/(W*L),1)
	return [img_jpg, percents]
