
# Import packages
from __future__ import division
import random
from PIL import Image
import time
from datetime import datetime
import os


def create_gameset_picture(EGParameters,gameset_pic_list,gameset_pic_name,width,height):
  # each image associated to games of the game set are opened, resized to width,height and paste in the imgNew of the game set 
  imNew=Image.new("RGB" ,(width*EGParameters['columnNumber'],height*EGParameters['numGames']),0) 
  numgame=1
  for game_pic_list in gameset_pic_list:
    numimage=0
    for pic_name in game_pic_list:
      img=Image.open(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+EGParameters['estimationPicPath']+pic_name)))
      img=img.resize((width,height), Image.NEAREST)
      imNew.paste(img, (width*numimage,height*(numgame-1)))
      numimage=numimage+1
    numgame=numgame+1
  imNew = imNew.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=8)
  imNew.save(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+EGParameters['estimationPicPath']+gameset_pic_name)),format = 'PNG', colors=8)
      






