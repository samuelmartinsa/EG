# Only for square sizes
# s1 : size of image m1
# s2 : size of image m2
# pos: position tuple
# @ post: insert m2 into m1 at position pos
#def insert_im(m1,m2,pos,s1,s2):

# Import packages
from __future__ import division
import random
from PIL import Image, ImageDraw
import math
from datetime import datetime, timedelta
import time
import os
def peanuts_light(probability,picPath,estimationPicPath,pic_name):
  nbpeanuts=0
  tab_geometricshape={0:'circle',1:'rectangle',2:'cross'}
  tab_color={0:(255,0 ,0),1:(0 ,255,0),2:(0,0 ,255),3:(255 ,255,0),4:(255,0 ,255),5:(0 ,255,0),6:(0 ,255,255),7:(0 ,0,255)}
  img=Image.new("RGB" ,(200,200),(255,255,255)) 
  nbline=20
  nbcol=20
  celldim=10
  offset=0
  draw = ImageDraw.Draw(img)
  geometricshape=tab_geometricshape[random.randint(0,len(tab_geometricshape)-1)]
  geometricshapecolor1=tab_color[random.randint(0,len(tab_color)-1)]
  geometricshapecolor2=(255,255,255)
  tab_geometricshapecolor={0:geometricshapecolor1,1:geometricshapecolor2}
  for numcol in range(nbcol):
    for numline in range(nbline):
      for i in range(0,2):
        if(random.uniform(0,1)<probability):
          nbpeanuts=nbpeanuts+1;
          if(random.randint(0,1)==1):
            offset=random.randint(1+i,1+2*i)
            if(random.randint(0,1)==1):
              offset=-offset
          if(geometricshape=='circle'):
            draw.ellipse((celldim*numcol+offset,celldim*numline+offset ,celldim*numcol+offset+7-2*i,celldim*numline+offset+7-2*i), tab_geometricshapecolor[i],(0,0,0))
          if(geometricshape=='rectangle'):
            draw.rectangle((celldim*numcol+offset,celldim*numline+offset ,celldim*numcol+offset+7-2*i,celldim*numline+offset+7-2*i), tab_geometricshapecolor[i],(0,0,0))
          if(geometricshape=='cross'):
            draw.rectangle((celldim*numcol+offset,celldim*numline+offset ,celldim*numcol+offset+2,celldim*numline+offset+9), tab_geometricshapecolor[i],(0,0,0))
            draw.rectangle((celldim*numcol+offset-4,celldim*numline+offset+5 ,celldim*numcol+offset+6,celldim*numline+offset+3), tab_geometricshapecolor[i],(0,0,0))
            # suppress segments of intersection border lines of the second segment (horizontal) over the first segment (vertical
            draw.rectangle((celldim*numcol+offset+1,celldim*numline+offset+1 ,celldim*numcol+offset+2-1,celldim*numline+offset+9-1), tab_geometricshapecolor[i],None)
  del draw
  # write to stdout
  img.save(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+estimationPicPath+pic_name)),format = 'PNG', colors=8)
  return nbpeanuts
