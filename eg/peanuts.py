# Only for square sizes
# s1 : size of image m1
# s2 : size of image m2
# pos: position tuple
# @ post: insert m2 into m1 at position pos
#def insert_im(m1,m2,pos,s1,s2):

# Import packages
from __future__ import division
import random
from PIL import Image
import math
import time
import os
#from images2gif import writeGif
#from scipy import misc : not installed on Windows (and  not used : only to create gif)


def peanuts(low,high,picPath,estimationPicPath):
  ### 1 - Moving and pictures parameters
  pic_num = random.randint(10000000,99999999);
  deltaT = 1/6    # Time resolution
  T = 6        # Total time
  Npix = int(math.floor(T/deltaT))  # Number pix generated
  
  # a) Background
  s1 = 500              
  tup_size = s1,s1
  L1 = s1*s1
  m1 = [ (255,255,255) for i in range(L1) ] 
  
  # b) Peanut 2
  s2 = 25        # Peanut 2 size
  n2 = random.randint(low, high)        # Number of peanuts 1
  max_bound2 = math.floor(math.sqrt(s1-s2-1)) # Used for quadratic distribution
  #max_bound2 = s1-s2
  # Importing picture
  original2 = Image.open(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+picPath+"peanut.png")))
  m2 = list(original2.getdata())
  
  # ** Magic formula to suppress a black line
  for i in range(s2):
    m2[i*(s2)+i-1] = (255,255,255)  
  
  # ** Initial peanut's position
  x_init2 = [ 0 for i in range(n2) ] # Peanut's X-positions
  y_init2 = [ 0 for i in range(n2) ] # Peanut's Y-positions
  x2 = [ 0 for i in range(n2) ] # Peanut's X's for input
  y2 = [ 0 for i in range(n2) ] # Peanut's Y's for input
  L  = [ 0 for i in range(n2) ]
  M  = [ 0 for i in range(n2) ]
  signy  = [ 0 for i in range(n2) ]

  security = 20

  for i in range(n2):
    x_init2[i] = random.randint(1,max_bound2)
    x_init2[i] = x_init2[i]*x_init2[i]     # Quadratic distribution
    y_init2[i] = random.randint(1,max_bound2)
    y_init2[i] = y_init2[i]*y_init2[i]     # Quadratic distribution
  #  l_bound = max(1,min(s1 - y_init2[i]-security,y_init2[i] - security))
  #  m_bound = max(1,min(s1 - x_init2[i]-security,x_init2[i] - security))
    l_bound = max(1,s1 - y_init2[i]-security)
    m_bound = max(1,s1 - x_init2[i]-security)
    L[i] = random.randint(1,l_bound)   # Random move
    M[i] = random.randint(1,m_bound)   # Random move
    signy[i] = random.randint(1,2)
    x2[i] = x_init2[i]
    y2[i] = y_init2[i]

  ### 2 - Generating pictures
  images = []
  t = 0
  k=1;#for k in range(Npix):
  t = t + deltaT
  m1 = [ (255,255,255) for i in range(L1) ] # new background
  for j in range(n2):
    # Time update positions
    if (t <= T/2):
      x_init2[j] = x_init2[j] + int(math.floor(2*(deltaT/T)*M[j]))
      y_init2[j] = y_init2[j] + int(math.pow(-1,signy[j]))*int(math.floor(2*(deltaT/T)*L[j]))
      x2[j] = x_init2[j]
      y2[j] = y_init2[j]
    else:
      x_init2[j] = x_init2[j] - int(math.floor(2*(deltaT/T)*M[j]))
      y_init2[j] = y_init2[j] - int(math.pow(-1,signy[j]))*int(math.floor(2*(deltaT/T)*L[j]))
      x2[j] = x_init2[j]
      y2[j] = y_init2[j]
    
    # Start counter for including image in background
    cnt = 0
    for i in m2:
      error = (255 - i[0]) + (255 - i[1]) + (255 - i[2])
      tol = 0.25;
      error_rate = error/(255^3);
      if error_rate > tol:
#          if (y2[j] < 0 or y2[j] > s1):
#            print y2[j]
#          if (x2[j] < 0 or x2[j] > s1):
#            print x2[j]
        m1[min(L1-1,y2[j] + s1*x2[j])] = i
      cnt = cnt + 1
      if cnt == s2+1:
        y2[j] = y_init2[j]
        x2[j] = x2[j] + 1
        cnt = 0
      else:
        y2[j] = y2[j] + 1
  
  # Saving big image
  imNew=Image.new("RGB" ,tup_size) 
  imNew.putdata(m1) 
  pic_name = str(pic_num)+".png"
  imNew.save(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+estimationPicPath+pic_name)),format = 'PNG')
  #imNew.save(pic_name,format = 'PNG')
  #imRead = misc.imread(pic_name)
  #images.append(imRead)
  imageElementsNumber=str(n2)
  return [pic_name,imageElementsNumber,'',0]  



