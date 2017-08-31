# Spirale i,j
import math 

def spirale(img_jpg):
	UP = 0
	LEFT = 1
	DOWN = 2
	RIGHT = 3

	W = int(math.sqrt(len(img_jpg)))
	L = W

	i = (W - 1)/2 # center
	j = (L - 1)/2 # center

	actual_state = UP 
	count = 0
	state_count = 0
	gen_count = 0;
	n = 0
	color_state = img_jpg[j + i*L]
	complexity = 0

	while (i >= 0 and i < W and j >= 0 and j < L):
		gen_count += 1;
		#print(str(gen_count)+" ["+str(i)+","+str(j)+"] n ="+str(n))	
			
		if actual_state == UP:
			i -= 1 
		elif actual_state == LEFT:
			j -= 1 
		elif actual_state == DOWN:
			i += 1
		else:
			j += 1
				
		count += 1
		
	
		if count > n:
			actual_state = (actual_state + 1) % 4
			state_count += 1
			count = 0
			
		if state_count > 1:
			n += 1
			state_count = 0
		
		if img_jpg[j + i*L] != color_state:
			color_state = img_jpg[j + i*L]
			complexity += 1
		
	return complexity
	
