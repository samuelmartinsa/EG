from fractale_new import fractale_new
import random

def fractale_complex(picPath,pic_name):
	param = False
	while (not param):
		out = fractale_new(picPath,pic_name)
		param = out[2]
	return [out[0],out[1],out[3]]
