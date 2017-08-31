import os
from PIL import Image, ImageDraw, ImageFont

def createRoundImages(listRoundValues,sessionId,workerId,gameId,roundId,distinct,tmpPicPath,xMax,imgHeight,imgWidth,zoom,xLabelFormat,graduationStep1,graduationStep2,estimationPointSize) :
  zoomedImgWidth=imgWidth*zoom
  ratio=(imgWidth/xMax)*zoom
  xAxisPos=imgHeight/2
  imgNumber_of_one_round = 0
  # The choice of WorkerId must be printed and not hidden with the choice of an other worker : printed after others players prints 
  xWorkerId=xMax+1 
  try : # works on windows systems : Python gets TTF from Windows\Fonts. OS and installation dependant on Linux
    font = ImageFont.truetype("arial.ttf", 16)
  except :
    font = ImageFont.load_default()
  for oneEvaluatedImg in listRoundValues :
    img_prevround = Image.new("RGB",(zoomedImgWidth,imgHeight),color = (255,255,255))
    imgNumber_of_one_round = imgNumber_of_one_round + 1
    draw = ImageDraw.Draw(img_prevround)
    # x axis
    draw.rectangle((0,xAxisPos,zoomedImgWidth,xAxisPos+1),fill=255,outline=255)
    for x in range(int(xMax)) :
      draw.line((x*ratio,xAxisPos-2,x*ratio,xAxisPos),fill=1024)
      if x%graduationStep1 == 0 :
        draw.rectangle((x*ratio-1,xAxisPos-4,x*ratio+1,xAxisPos),fill=1024)
        textSize=draw.textsize(str(x), font=font)
        textWidth = textSize[0]
        draw.text((x*ratio-textWidth/2, xAxisPos+5), xLabelFormat.format(x),fill=(0,0,0), font=font);
      if x%graduationStep2 == 0 :
        draw.rectangle((x*ratio-1,xAxisPos-8,x*ratio+1,xAxisPos),fill=1024)
        textSize=draw.textsize(str(x), font=font)
        textWidth = textSize[0]
        draw.text((x*ratio-textWidth/2, xAxisPos+5), xLabelFormat.format(x),fill=(0,0,0), font=font);
    # round responses values over the x axis
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
