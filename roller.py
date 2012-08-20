import random

def roll_four():
	sum = 0
	for i in range(0,4):
		sum += random.randint(-1,1)
	return sum
