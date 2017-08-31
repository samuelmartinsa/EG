# Entropy i,j
import math 

def entropy(percents):	
	if percents[0] < 5 or percents[1] < 5 or percents[2] < 5:
		return 0
	else:
		complexity = -( percents[0]*math.log10(percents[0]/100) 
				   + percents[1]*math.log10(percents[1]/100)
				   + percents[2]*math.log10(percents[2]/100))/100
				   
		maxc = - math.log10(0.3)
		return round(complexity/maxc,2)
	
