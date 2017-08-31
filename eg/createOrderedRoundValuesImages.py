import os
from PIL import Image, ImageDraw, ImageFont

def createOrderedRoundValuesImages(listRoundValues,sessionId,workerId,gameId,roundId,tmpPicPath,imgWidthMax) :
  imgNumber_of_oneSortedListOfDecisions = 0
  # The choice of WorkerId must be printed and not hidden with the choice of an other worker : printed after others players prints 
  try : # works on windows systems : Python gets TTF from Windows\Fonts. OS and installation dependant on Linux
    font = ImageFont.truetype("arial.ttf", 12)
  except :
    font = ImageFont.load_default()
  # calculate best width and height for images : depend on text representation with the chosen font  
  img = Image.new("RGBA",(100,100),color = (255,255,255))
  
  draw = ImageDraw.Draw(img)
  textWidth=0
  textHeight=0
  for oneListOfDecisions in listRoundValues :
    numberOfDecisions=0
    for decisionValue in oneListOfDecisions:
      numberOfDecisions=numberOfDecisions+1
      textSize=draw.textsize(str(decisionValue), font=font)
      textWidth = max(textSize[0],textWidth)
      textHeight= max(textSize[1],textHeight)
    ## end for
  ## end for
  imgWidth=(4+textWidth+4)*numberOfDecisions
  imgHeight=4+textHeight+4
  oneDecisionRectWidth=textWidth+4
  oneDecisionRectHeight=imgHeight
  spaceBetweenDecisionRect=2
  del draw
  for oneListOfDecisions in listRoundValues :
    imgNumber_of_oneSortedListOfDecisions= imgNumber_of_oneSortedListOfDecisions + 1
    workerIdDecisionValue=oneListOfDecisions[int(workerId)-1]
    oneSortedListOfDecisions=sorted(oneListOfDecisions)
    # oneListOfDecisions is sorted and the index workerId isn't the same in oneSortedListOfDecisions
    # we walk through oneSortedListRoundValues, find the decision value (the first one if several is convenient) and fix the numDecision index
    numDecision=1
    for decisionValue in oneSortedListOfDecisions:
      if decisionValue==workerIdDecisionValue:
        break
      else:
        numDecision=numDecision+1
    ## end for
    img_oneSortedListOfDecisions = Image.new("RGB",(imgWidth,imgHeight),color = (0,0,0, 0))
    draw = ImageDraw.Draw(img_oneSortedListOfDecisions)
    # round responses values 
    id=0
    x0=0
    x1=-2
    for oneValue in oneSortedListOfDecisions :
      id=id+1
      x0 = x1+spaceBetweenDecisionRect
      y0 = 0
      x1 = x0+oneDecisionRectWidth
      y1 = oneDecisionRectHeight
      if numDecision == id :
        textColor=(255,0,0)
      else :
        textColor=(0,0,0)
      draw.rectangle([x0, y0, x1, y1],(170,200,255),outline=(170,200,255))
      draw.text((x0+2,2), str(oneValue),fill=textColor, font=font);
    ## end for  
    del draw
    img_oneSortedListOfDecisions.save(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+tmpPicPath+'img_oneSortedListOfDecisions_'+str(gameId)+'_'+str(roundId)+'_'+str(imgNumber_of_oneSortedListOfDecisions)+'_'+str(sessionId)+'.gif'), "GIF", transparency=0)	
