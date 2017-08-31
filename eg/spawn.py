import os,sys
import argparse

parser = argparse.ArgumentParser(description='Estimation game robots')
parser.add_argument('-n','--numRobots',  help='number of Robots', default=2)
parser.add_argument('-m','--do_multiget',  help='do get', default='y')
args = parser.parse_args()
numRobots=int(args.numRobots)
do_multiget=args.numRobots
mg=''
if(do_multiget=='y'):
  mg='mg'
for n in range(0,numRobots):
  os.spawnl(os.P_NOWAIT, r'C:\Program Files (x86)\PHP\php','php', 'robot_eg.php '+mg)
