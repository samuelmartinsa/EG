import os
from PIL import Image, ImageDraw, ImageFont

def createOrderedListChoicesImages(listRoundValues,sessionId,workerId,gameId,roundId,tmpPicPath,imgHeight,imgWidth) :
  imgNumber_of_one_round = 0
  # The choice of WorkerId must be printed and not hidden with the choice of an other worker : printed after others players prints 
  try : # works on windows systems : Python gets TTF from Windows\Fonts. OS and installation dependant on Linux
    font = ImageFont.truetype("arial.ttf", 16)
  except :
    font = ImageFont.load_default()
  for oneEvaluatedImg in listRoundValues :
    workerIdDecisionValue=oneEvaluatedImg[workerId]
    img_prevround = Image.new("RGB",(imgWidth,imgHeight),color = (255,255,255))
    imgNumber_of_one_round = imgNumber_of_one_round + 1
    draw = ImageDraw.Draw(img_prevround)
    # round responses values 
    id=0
    for oneValue in oneEvaluatedImg :
      id=id+1
      x = oneValue*ratio
      x0 = x-estimationPointSize/2
      y0 = 10-estimationPointSize/2
      x1 = x+estimationPointSize/2
      y1 = 10+estimationPointSize/2
      if int(workerId) == id :
        xWorkerId=x
      else :
        draw.ellipse([x0, y0, x1, y1],fill=(0,0,255),outline=(0,0,255))
    draw.ellipse([xWorkerId-estimationPointSize/2, 10-estimationPointSize/2, xWorkerId+estimationPointSize/2, 10+estimationPointSize/2],fill=(255,0,0),outline=(255,0,0))
    del draw
    img_prevround.save(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+tmpPicPath+'img_prevround_'+str(gameId)+'_'+str(roundId)+'_'+str(imgNumber_of_one_round)+'_'+str(sessionId)+distinct+'.jpg'), "JPEG")	
