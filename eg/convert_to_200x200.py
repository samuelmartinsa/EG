import os
from PIL import Image
import time
from datetime import datetime
from sqlalchemy import create_engine
from config import config

port=config.get('Database Parameters', 'port')
host=config.get('Database Parameters', 'host')
login_username=config.get('Database Parameters', 'login_username')
login_pw=config.get('Database Parameters', 'login_pw')
database_name=config.get('Database Parameters', 'database_name')
DATABASE_SERVER="mysql://"+login_username +":"+login_pw+"@"+host+":"+port+"/"
DATABASE = DATABASE_SERVER+database_name
engine = create_engine(DATABASE, echo=False)
rs=[]
rs.append("/20140609-232827-377000.png")
rs.append("/20140609-232827-837000.png")
rs.append("/20140609-232828-198000.png")
#query_rs="select pic_name from image" 
#rs=engine.execute(query_rs)
print os.path.normpath(os.path.abspath(os.path.dirname(__file__))+"/static/pic/estimationPic/20140609-232828-198000.png")
for pic_name in rs:
  imNew=Image.new("RGB" ,(200,200),0) 
  #img=Image.open(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+"/static/pic/estimationPic/"+row_rs['pic_name'])))
  img=Image.open(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+"/static/pic/estimationPic/"+pic_name))
  img=img.resize((200,200), Image.NEAREST)
  imNew.paste(img, (0,0))
  #img=img.resize((10, 10), Image.NEAREST)
  imNew.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=8)
  #img.save(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+"/static/pic/estimationPic/"+row_rs['pic_name'])),format = 'PNG', colors=8)
  imNew.save(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+"/static/pic/estimationPic/"+pic_name+"-1"),format = 'PNG', colors=8)    






