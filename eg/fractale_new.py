# Packages
from __future__ import division
import random
from PIL import Image
import math
import time
import os
from spirale import spirale
from entropy import entropy
from pixelize import pixelize


def fractale_new(picPath,pic_name):
  
  percent = 0       # percentage color 1 - initialize
  percent2 = 0     # percentage color 2 - initialize
  percent3 = 0      # percentage color 3 - initialize
  high_threshold = 95  # max percentage number
  low_threshold = 5   # min percentage number
  n_max = 8       # avoid infinite loop
  n = 0          # loop initialization
  smallness = 2      # 1 = big --> 4 tiny
  n_lakes = 2       # number of models
  iteration_max = 20   # fractale convergence factor
  speed = 2        # speed of generation (high speed = low picture size)
  sp = 0          # separation between models
  
  # Zone definition
  x1_i = -1.2
  x2_i = 0.6
  y1_i = -1
  y2_i = 1
  
  # Image size
  image_x = int(270/speed)
  image_y = int(270/speed)
  
  # Complexity param
  spirale_r = 700
  entropy_r = 0.2
  
  
  # Random parameter lists
  p1 = []   # initial cr
  p2 = []   # initial ci
  k = []     # multiplication factor
  phi = []   # rotation
  cx = []   # center x
  cy = []   # center y
  ampx = []   # amplitude x
  ampy = []   # amplitude y
  
  # Lake-dependent parameters
  x1 = []
  x2 = []
  y1 = []
  y2 = []
  zoom_x = []
  zoom_y = []
  
  c_r = [0 for i in range(n_lakes)]
  c_i = [0 for i in range(n_lakes)]
  z_r = [0 for i in range(n_lakes)]
  z_i = [0 for i in range(n_lakes)]
  
  # Colors
  dark_blue = [(0,0,139),'dark-blue']
  red = [(255,0,0),'red']
  light_blue = [(135,206,250),'light-blue']
  yellow = [(252,248,0),'yellow']
  green = [(27,169,80),'green']
  purple = [(169,29,129),'purple']
  black = [(0,0,0),'black']
  colors = [dark_blue,red,light_blue,yellow,green,purple]
  
  color_to_find = colors.pop(random.randint(0, 5))
  color2 = colors.pop(random.randint(0, 4))
  color3 = colors.pop(random.randint(0, 3))
  big = random.randint(0,1)
  
  t1 = time.time()
  
  while (n < n_max and (percent > high_threshold or percent < low_threshold)):
  
    for i in range(n_lakes):
    
      # Random probabilities 
      p1.append(random.random()) # initial condition 1
      p2.append(random.random()) # initial condition 2
      k.append(random.uniform(0.7,1))
      phi.append(random.uniform(0,1))  # rotation
      if i%3 == 0:
        posx = x1_i + 0.25*(x2_i - x1_i)
        posy = y1_i + 0.25*(y2_i - y1_i)
      elif i%3 == 1:
        posx = x1_i + 0.75*(x2_i - x1_i)
        posy = y1_i + 0.75*(y2_i - y1_i)
      else:
        posx = x1_i + 0.25*(x2_i - x1_i)
        posy = y1_i + 0.75*(y2_i - y1_i)
      cx.append(random.uniform(posx-sp,posx+sp)) # center x
      cy.append(random.uniform(posy-sp,posy+sp)) # center y
              
      ampx.append(random.uniform(0.15*(x2_i - x1_i),smallness*(x2_i - x1_i)))
      ampy.append(random.uniform(0.15*(y2_i - y1_i),smallness*(y2_i - y1_i)))
      
  #    print "p1 = "+str(p1[i])+" p2 = "+str(p2[i])+" k = "+str(k[i])+" "
  #    print "phi = "+str(phi[i])+" (cx,cy) = ("+str(cx[i])+","+str(cy[i])+") "
  #    print " (ampx,ampy) = ("+str(ampx[i])+","+str(ampy[i])+") "
    
      # Redefine zone
      x1.append(cx[i] - ampx[i])
      x2.append(cx[i] + ampx[i])
      y1.append(cy[i] - ampy[i])
      y2.append(cy[i] + ampy[i])
  
  
      ## Create fractale matrix - Inspired from siteduzero
      # Compute image size
  
      zoom_x.append(image_x/(x2[i] - x1[i]))
      zoom_y.append(image_y/(y2[i] - y1[i]))
  
    # Initialisation
    x = 0
    y = 0
    count = 0  # color1
    count2 = 0 # color2
    count3 = 0 # color3
    Le = image_x * image_y
    img = [ [ 0 for i in range(image_y) ] for j in range(image_x) ]
    img_jpg = [ 0 for i in range(Le) ]
  
    # Black image initially
    for i in range(Le):
      img_jpg[i] =  black[0] 
  
    # Fill matrix
    while x < image_x :
      y = 0
      while y < image_y :
        
        bool = False
        for j in range(n_lakes):
          c_r[j] = x / zoom_x[j] + x1[j]
          c_i[j] = y / zoom_y[j] + y1[j]
          z_r[j] = p1[j]
          z_i[j] = p2[j]
          bool = bool or z_r[j]*z_r[j] + z_i[j]*z_i[j] < 4
  
        i = 0
        var = True
        
        while var or (bool and i < iteration_max):
          
          bool = False
          for j in range(n_lakes):
          
            if j%3 == 0:   
              
              z_r[j] = (z_r[j]*z_r[j] - z_i[j]*z_i[j])*k[j] + c_r[j]
              z_i[j] = 2*z_i[j]*z_r[j] + c_i[j] * k[j]
            elif j%3 == 1:
              z_r[j] = z_r[j]*z_r[j]*z_r[j]*z_r[j] + 6*z_r[j]*z_r[j]*z_i[j]*z_i[j] + z_i[j]*z_i[j]*z_i[j]*z_i[j] + k[j]*c_r[j]
              z_i[j] = 4*z_r[j]*z_r[j]*z_r[j]*z_i[j] + 4 *z_r[j]*z_i[j]*z_i[j]*z_i[j] + k[j]*c_i[j]
            else:
              z_r[j] = z_r[j]*z_r[j]*z_r[j] - 3*z_r[j]*z_i[j]*z_i[j] + k[j]*c_r[j]
              z_i[j] = 3*z_r[j]*z_r[j]*z_i[j] - z_i[j]*z_i[j]*z_i[j] + k[j]*c_i[j]
            
            # Rotation
            z_r[j] = z_r[j]*math.cos(phi[j]) - z_i[j]*math.sin(phi[j])
            z_i[j] = z_r[j]*math.sin(phi[j]) + z_i[j]*math.cos(phi[j])
            bool = bool or z_r[j]*z_r[j] + z_i[j]*z_i[j] < 4
          
          i = i+1
          var = False
          
        if i == iteration_max:
          if big:
            img_jpg[x + image_x*y] = color_to_find[0]
            count += 1
          else:
            img_jpg[x + image_x*y] = color2[0]
            count2 += 1
        elif i > iteration_max/10:
          img_jpg[x + image_x*y] = color3[0]
          count3 += 1        
        elif i > iteration_max/20:
          img_jpg[x + image_x*y] = color_to_find[0]
          count += 1
        else:
          if big:
            img_jpg[x + image_x*y] = color2[0]
            count2 += 1
          else:
            img_jpg[x + image_x*y] = color3[0]
            count3 += 1
        y = y + 1
      x = x + 1
  
    percent = round(100*count/Le)
    percent2 = round(100*count2/Le)
    percent3 = 100 - percent - percent2
    n = n + 1
  
  
#  print("To find: "+color_to_find[1]+"-percentage = "+str(percent)+"%")
#  print("Other: "+color2[1]+"-percentage = "+str(percent2)+"%")
#  print("Other: "+color3[1]+"-percentage = "+str(percent3)+"%")
  
  # Evaluate complexity
  percents = [percent, percent2, percent3]
  spir = spirale(img_jpg)
  entr = entropy(percents)
#  print("Spirale :"+str(spir))
#  print("Entropy :"+str(entr))
  
  # Time
  t2 = time.time()
  t = t2-t1
  
  # Convert to png
  if spir > spirale_r and entr > entropy_r:
    out = pixelize(img_jpg,[color_to_find[0], color2[0], color3[0]])
    img_jpg = out[0]
    percents_new = out[1]
    tup_size = image_x,image_y
    imNew=Image.new("RGB" ,tup_size) 
    imNew.putdata(img_jpg)
    imNew = imNew.resize((200, 200), Image.NEAREST) 
    try:
      imNew.save(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+picPath+str(pic_name)),format = 'PNG')
    except:
      print "Saving image failed"
      
    return [percents_new[0],color_to_find[1],True,spir]
    
  return [-1,(0,0,0),False,0]
