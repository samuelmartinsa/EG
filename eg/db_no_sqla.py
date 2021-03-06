import random
from datetime import date,datetime, timedelta
import time
import MySQLdb
import sys
import os
import json
from config import config
import subprocess

host=config.get('Database Parameters', 'host')
port=config.get('Database Parameters', 'port')
login_username=config.get('Database Parameters', 'login_username')
login_pw=config.get('Database Parameters', 'login_pw')
database_name=config.get('Database Parameters', 'database_name')
dump_command=config.get('Server Parameters', 'dump_command')
paramMysql = {'host':host,'port':int(port),'user':login_username,'passwd':login_pw, 'db':database_name}
connection = MySQLdb.connect(**paramMysql)
connection.autocommit = True
cursor = connection.cursor(MySQLdb.cursors.DictCursor)
cursor_without_keys = connection.cursor()

def init_db_connection():
  global connection, cursor, cursor_without_keys
  host=config.get('Database Parameters', 'host')
  port=config.get('Database Parameters', 'port')
  login_username=config.get('Database Parameters', 'login_username')
  login_pw=config.get('Database Parameters', 'login_pw')
  database_name=config.get('Database Parameters', 'database_name')
  paramMysql = {'host':host,'port':int(port),'user':login_username,'passwd':login_pw, 'db':database_name}
  if( not connection.open): 
    connection = MySQLdb.connect(**paramMysql)
  connection.autocommit = True
  cursor = connection.cursor(MySQLdb.cursors.DictCursor)
  cursor_without_keys = connection.cursor()
  return connection,cursor,cursor_without_keys

def init_db():
  print "create database "+database_name
  cursor.execute("drop database if exists "+database_name)
  connection.commit()
  cursor.execute("create database "+database_name)
  connection.commit()
  init_db_file=open(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+'/init_db.sql')))
  for query in init_db_file:
    cursor.execute(query)
    connection.commit()

def GetSQLValueString(theValue, theType):
  if theValue==None:
    return 'NULL'
  if(theType=='text') :
    theValue=str(theValue)
    theValue=theValue.replace("\\","\\\\")
    theValue=theValue.replace("'","\\'") 
    theReturnValue="'" + theValue + "'"
  else :
    try :
      theReturnValue=str(theValue)
    except :
      theReturnValue=None
  return theReturnValue;

def dump_db(filePath):
  print 'dump_db()',dump_command,os.path.normpath(os.path.abspath(os.path.dirname(__file__))+filePath+'dump_db')+'.sql' 
  subprocess.call(dump_command+' -u '+login_username+' -p'+login_pw+' '+database_name+'>'+os.path.normpath(os.path.abspath(os.path.dirname(__file__))+filePath+'dump_db')+'.sql', shell=True)
  return
    
def free_images() :
  query="select * from image where status=2" 
  cursor.execute(query)
  rows=cursor.fetchall()
  for row in rows:
    query="insert into image (pic_name,percent,complexity,color,pic_type,status)"+\
              " values ('"+row['pic_name']+"',"+str(row['percent'])+","+str(row['complexity'])+",'"+row['color']+"','"+row['pic_type']+"',1)"
    cursor.execute(query)
    connection.commit()
  return

def generateNewKeyCodes(numberOfNewKeyCodes):
  i=0
  while i < numberOfNewKeyCodes:
    try:
      query="insert into keycode_gameset_user (keyCodeBegin,creationtime,usagetime,userid,gamesetid,keyCodeEnd,status,bonus) values ('"+str(random.randint(10000000, 99999999))+"','"+str(datetime.now())+"','"+str(datetime.now())+"',-1,-1,'"+str(random.randint(10000000, 99999999))+"','','')"
      cursor.execute(query)
      connection.commit()
      i=i+1
    except:
      print 'random duplicate keyCodeBegin ? try again'
  return

def get_EG_session_info(EGParameters):
  content=''
  #user_logged
  localtimeadjust=datetime.now()-datetime.utcnow()
  query="(select username,lastvisit,'' as gamesetid,'' as num,'' as partstatus,keyCodeBegin,keycode_gameset_user.status as keycodestatus,bonus "+\
                 " from users, keycode_gameset_user"+\
                 " where users.id=keycode_gameset_user.userid and keycode_gameset_user.status='IN_USE' and gamesetid=-1"+\
                 " and lastvisit>'"+str(EGParameters['nextGameDate']+localtimeadjust)+"'"+\
                 " and usagetime>'"+str(EGParameters['nextGameDate']+localtimeadjust)+"'"+\
                 ")"+\
                 " UNION "+\
                 "(select username,lastvisit,keycode_gameset_user.gamesetid,if(games.num IS NULL,'',games.num) as num,"+\
                 " participant_statuslib as partstatus,keyCodeBegin,keycode_gameset_user.status as keycodestatus,bonus "+\
                 " from users,keycode_gameset_user,participants,participant_status,gamesets"+\
                 " left join games on (gamesets.id=games.gamesetid and games.status=2)"+\
                 " where users.id=keycode_gameset_user.userid and keycode_gameset_user.status='IN_USE' and keycode_gameset_user.gamesetid<>-1"+\
                 " and keycode_gameset_user.gamesetid=gamesets.id"+\
                 " and users.id=0+participants.workerId and gamesets.id=0+participants.assignmentId"+\
                 " and participants.status=participant_status.participant_statuscode"+\
                 " and lastvisit>'"+str(EGParameters['nextGameDate']+localtimeadjust)+"'"+\
                 " and usagetime>'"+str(EGParameters['nextGameDate']+localtimeadjust)+"'"+\
                 ")"+\
                 " UNION "+\
                 "(select username,lastvisit,keycode_gameset_user.gamesetid,'' as num,"+\
                 " participant_statuslib as partstatus,keyCodeBegin,keycode_gameset_user.status as keycodestatus,bonus "+\
                 " from users,keycode_gameset_user,gamesets, participants,participant_status"+\
                 " where users.id=keycode_gameset_user.userid and keycode_gameset_user.status='USED' and keycode_gameset_user.gamesetid<>-1"+\
                 " and keycode_gameset_user.gamesetid=gamesets.id"+\
                 " and users.id=0+participants.workerId and gamesets.id=0+participants.assignmentId"+\
                 " and participants.status=participant_status.participant_statuscode"+\
                 " and lastvisit>'"+str(EGParameters['nextGameDate']+localtimeadjust)+"'"+\
                 " and usagetime>'"+str(EGParameters['nextGameDate']+localtimeadjust)+"'"+\
                 ")"
                 #+\" order by lastvisit desc"
  cursor.execute(query)
  rows=cursor.fetchall()
  #game sets running
  content=content+"username"+"!#!"+"lastvisit"+"!#!"+"game set"+\
                  "!#!"+"game num"+"!#!"+"part status"+"!#!"+"key code"+"!#!"+"key code status"+"!#!"+"bonus"
  for row in rows:
    content=content+"###"  
    content=content+str(row["username"])+"!#!"+str(row["lastvisit"])+"!#!"+str(row["gamesetid"])+"!#!"+str(row["num"])+\
                  "!#!"+str(row["partstatus"])+"!#!"+str(row["keyCodeBegin"])+"!#!"+str(row["keycodestatus"])+"!#!"+str(row["bonus"])
  return content

def clean_tables_after_end_on_start():
  # delete gamesets with status UNUSED or WAITING_FOR_PARTICIPANTS and linked games, participants, key codes. Free linked images
  query="select gamesets.id as gamesetid_to_stop from gamesets where status=0 or status=1"
  cursor.execute(query)
  rows=cursor.fetchall()
  for row in rows:
    gamesetid_to_stop=str(row['gamesetid_to_stop'])
    query="update image,games set image.gameid=NULL,image.status=1 where image.gameid=games.id and games.gamesetid="+gamesetid_to_stop
    cursor.execute(query)
    connection.commit()
    # query="delete from games_participants where assignmentId='"+gamesetid_to_stop+"'"
    # cursor.execute(query)
    # connection.commit()
    # query="delete from gamesets_participants where assignmentId='"+gamesetid_to_stop+"'"
    # cursor.execute(query)
    query="delete from participants where assignmentId='"+gamesetid_to_stop+"'"
    cursor.execute(query)
    connection.commit()
    query="delete from games where gamesetid="+gamesetid_to_stop
    cursor.execute(query)
    connection.commit()
    query="delete from gamesets where id="+gamesetid_to_stop
    cursor.execute(query)
    connection.commit()
    query="delete from keycode_gameset_user where gamesetid="+gamesetid_to_stop
    cursor.execute(query)
    connection.commit()
  ## end for
  # update gamesets with status STARTED to status TERMINATED 
  query="update gamesets set status=3 where status=2"
  cursor.execute(query)
  connection.commit()
  # update games with status STARTED to status TERMINATED 
  query="update games set status=3 where status=2"
  cursor.execute(query)
  connection.commit()
  # update keycodes with status=IN_USE to status USED
  query="update keycode_gameset_user set status='USED' where status='IN_USE'"
  cursor.execute(query)
  connection.commit()
  # update users ip_in_use=no
  #query="update users set ip_in_use='n'"
  #cursor.execute(query)
  return

def get_db_users_gamesets():
  content=dict()
  query="(select users.id as userid,username,users.lastvisit as lastvisit, users.status as user_status,"+\
            " gamesets.id as gamesetid,gamesets.starttime as gameset_starttime,gamesets.status as gameset_status"+\
            " from users, participants, gamesets"+\
            " where users.id=0+participants.workerId and gamesets.id=0+participants.assignmentId and gamesets.status<>3"+\
            ") union"+\
            "(select users.id as userid,username,users.lastvisit as lastvisit, users.status as user_status,'' as gamesetid,'' as gameset_starttime,'' as  gameset_status"+\
            " from users"+\
            " where users.status<>4"+\
            ")"+\
            " order by gamesetid,gameset_starttime"
  cursor.execute(query)
  rows=cursor.fetchall()
  content[0]=(('User Id','Username','lastvisit','user_status','Gameset Id','gameset_starttime','gameset_status'))
  i=1
  for row in rows:
    content[i]=row
    i=i+1
  return content

def get_db_keys_users_gamesets() :
  content=dict()
  key='keycode'
  content[key]=dict();
  query= "select keyCodeBegin, keyCodeEnd, if(users.username IS NULL,'',users.username) as username,"+\
            " if(gamesets.id IS NULL,'',gamesets.id) as gamesetid,"+\
            " if(gamesets.job_id IS NULL,'',gamesets.job_id) as job_id,bonus, if(totalreward IS NULL,'',totalreward) as totalreward,"+\
            " if(keycode_gameset_user.status='' or keycode_gameset_user.userid=-1 or keycode_gameset_user.gamesetid=-1,"+\
                  "'',"+\
                  "if(keycode_gameset_user.status='PAID','USED','PAID')) as submitvalue, "+\
            " keycode_gameset_user.status"+\
            " from keycode_gameset_user left join users on keycode_gameset_user.userid=users.id"+\
            " left join gamesets on keycode_gameset_user.gamesetid=gamesets.id"+\
            " order by keycode_gameset_user.gamesetid,users.username asc"
  cursor_without_keys.execute(query)
  rows=cursor_without_keys.fetchall()
  i=1
  content[key][i]=(('keyCodeBegin','keyCodeEnd','User','Gameset Id','job_id','bonus','Total Reward','','status'))
  i=2
  for row in rows:
    content[key][i]=row
    i=i+1
  return content

def db_get_free_keys() : 
  result=""
  query= "select keyCodeBegin, keyCodeEnd from keycode_gameset_user where userid=-1 and gamesetid=-1"
  cursor.execute(query)
  rows=cursor.fetchall()
  result=result+'keyCodeBegin,keyCodeEnd\n'
  for row in rows:
    result=result+row['keyCodeBegin']+','+row['keyCodeEnd']+'\n'
  return result
  
def check_for_enough_games(EGParameters):
  gamesList=dict()
  goodGamesList=dict()
  # all the games having characteristics of the required game parameters
  query="select games.* from games,gamesets"+\
            " where games.gamesetid=gamesets.id and gamesets.numExpectedParticipants="+str(EGParameters['numExpectedParticipants'])+\
            " and gamesets.playmode="+GetSQLValueString(EGParameters['playMode'], "text")
  cursor.execute(query)
  rows=cursor.fetchall()
  first = True
  for row in rows:
    gamesList[row['id']]=row['id']
  good_game_id_file=open(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+'/good_game_id.csv'))
  found=False
  num_good_games=0
  for a_good_game_id in good_game_id_file:
    a_good_game_id=a_good_game_id.strip("\n")
    if a_good_game_id[0:9]=='pic_type:' :
      pic_type=a_good_game_id[9:]
      if pic_type==EGParameters['imageType'] :
        found=True
      else :
        if found:
          break
    elif a_good_game_id !='' and a_good_game_id !=None and found :
      if int(a_good_game_id) in gamesList :
        goodGamesList[num_good_games]=int(a_good_game_id)
        num_good_games=num_good_games+1
  # enough games 
  if num_good_games>=EGParameters['numGames']:
    return True
  else :
    return False



def select_and_create_games(EGParameters,gamesetid):
  content=dict()
  gameset=dict()
  gamesList=dict()
  goodGamesList=dict()
  tab_of_goodImages=dict()
  tab_of_index_ordered_list_file=dict()
  tab_of_index=dict()
  tab_imageid=dict()
  tab_of_redundant_images=dict();# 20150502 : redundant images
  if EGParameters['redundantMode']=='y':
    numgame=1
    image_ordered_list_file=open(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+'/image_ordered_list.csv'))
    for a_line in image_ordered_list_file:
      an_ordered_line=a_line.strip("\n")
      index_list=an_ordered_line.split(",")
      tab_of_index_ordered_list_file[numgame]=dict()
      numcolumn=1
      for index in index_list:
        index=index.strip()
        tab_of_index_ordered_list_file[numgame][numcolumn]=index
        #print 'tab_of_index_ordered_list_file[numgame][numcolumn]',numgame,numcolumn,index
        numcolumn=numcolumn+1
      numgame=numgame+1
  # all the games having characteristics of the required gameset type
  query="select games.* from games,gamesets"+\
            " where games.gamesetid=gamesets.id and gamesets.numExpectedParticipants="+str(EGParameters['numExpectedParticipants'])+\
            " and gamesets.playmode="+GetSQLValueString(EGParameters['playMode'], "text")
  cursor.execute(query)
  rows=cursor.fetchall()
  first = True
  for row in rows:
    gamesList[row['id']]=row['id']
  good_game_id_file=open(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+'/good_game_id.csv'))
  found=False
  num_good_games=0
  for a_good_game_id in good_game_id_file:
    a_good_game_id=a_good_game_id.strip("\n")
    if a_good_game_id[0:9]=='pic_type:' :
      pic_type=a_good_game_id[9:]
      if pic_type==EGParameters['imageType'] :
        found=True
      else :
        if found:
          break
    elif a_good_game_id !='' and a_good_game_id !=None and found :
      if int(a_good_game_id) in gamesList :
        # discard games having an image already present in a selected game
        query="select distinct image.id as imageid,pic_name from image where gameid="+str(a_good_game_id)
        cursor.execute(query)
        rows=cursor.fetchall()
        discard=False
        for row in rows:
          if row['pic_name'] not in tab_of_goodImages:
            tab_of_goodImages[row['pic_name']]=row['pic_name']
          else:
            discard=True
#            print 'discard',a_good_game_id
        if not discard :
          goodGamesList[num_good_games]=int(a_good_game_id)
          num_good_games=num_good_games+1
  # EGParameters['numGames'] games from the goodGamesList
  rnd=random.sample(xrange(num_good_games), EGParameters['numGames'])
  for numgame in range(1,EGParameters['numGames']+1):
    gameid_to_replay=rnd[numgame-1]
    gameset[numgame]=dict()
    #gameset[numgame]['gameid_to_replay']=goodGamesList[gameid_to_replay]
    # create the game and select the new newgameid
    query="insert into games (num,status,numExpectedParticipants,numRounds,gamesetid)"+\
              " values ("+str(numgame)+",1,"+str(EGParameters['numExpectedParticipants'])+","+str(EGParameters['numRounds'])+","+str(gamesetid)+")"
    cursor.execute(query)
    connection.commit()
    cursor.execute("select max(id) as newgameid from games");# the last inserted game
    row=cursor.fetchone()
    newgameid=row['newgameid'] 
    gameset[numgame]['gameid']=int(newgameid)
    gameset[numgame]['game_pic_list']=list()
    # select the images linked to the selected gameid_to_replay and select decisions
    query="select distinct image.id as imageid,pic_name,percent,complexity,color,pic_type from rounds,choices,decisions,image"+\
                    " where rounds.id=choices.roundid and choices.id=decisions.choiceid and decisions.imageid=image.id and rounds.gameid="+str(goodGamesList[gameid_to_replay])+\
                    " order by choices.workerid,rounds.num,decisions.num"
    cursor.execute(query)
    rows=cursor.fetchall()
    numcolumn=1
    for row in rows:
      imageid=row['imageid']
      # tab_imageid : the matrix coordinates of each image
      tab_imageid[imageid]=dict()
      tab_imageid[imageid]['imageid']=imageid
      tab_imageid[imageid]['numgame']=numgame
      tab_imageid[imageid]['numcolumn']=numcolumn
      img_to_add=row
      if EGParameters['redundantMode']=='y':
        # index is the number given in the tab_of_index_ordered_list_file matrix of index
        index=tab_of_index_ordered_list_file[numgame][numcolumn]
        if index not in tab_of_index:
          tab_of_index[index]=img_to_add
        else:
          img_to_add=tab_of_index[index]
          # erase the tab_imageid matrix values with coordinates of the images to duplicate in some games
          imageid_to_copy=img_to_add['imageid']
          tab_imageid[imageid]['imageid']=imageid_to_copy
          tab_imageid[imageid]['numgame']=tab_imageid[imageid_to_copy]['numgame']
          tab_imageid[imageid]['numcolumn']=tab_imageid[imageid_to_copy]['numcolumn']
      query="insert into image (pic_name,percent,complexity,color,pic_type,status,gameid)"+\
                " values ('"+img_to_add['pic_name']+"',"+str(img_to_add['percent'])+","+str(img_to_add['complexity'])+",'"+img_to_add['color']+"','"+img_to_add['pic_type']+"',2,"+str(newgameid)+")"
      cursor.execute(query)
      connection.commit()
      gameset[numgame]['game_pic_list'].append(img_to_add['pic_name'])
      numcolumn=numcolumn+1      
    query="select image.id as imageid,decisions.choiceid,choices.workerid,rounds.num as roundnum,"+\
              " decisions.num as decisionnum,decisions.value as decisionvalue,TIME_TO_SEC(TIMEDIFF(decisions.timestamp,rounds.startTime)) as decisiontime"+\
              " from rounds,choices,decisions,image"+\
              " where rounds.id=choices.roundid and choices.id=decisions.choiceid and decisions.imageid=image.id and rounds.gameid="+str(goodGamesList[gameid_to_replay])+\
              " order by choices.workerid,rounds.num,decisions.num"
    cursor.execute(query)
    rows=cursor.fetchall()
    gameset[numgame]['game_workers_decisions']=dict()
    workerList=dict()
    num=0
    workernum=0
    for row in rows:
      if row['workerid'] not in workerList :
        num=num+1
        workernum=num
        workerList[row['workerid']]=workernum
      else:
        workernum=workerList[row['workerid']]
      #print 'select_and_create_games numgame',numgame,'workerid',row['workerid'],'workernum',workernum
      roundnum=int(row['roundnum'])
      decisionnum=int(row['decisionnum'])
      if workernum not in gameset[numgame]['game_workers_decisions'] :
        gameset[numgame]['game_workers_decisions'][workernum]=dict()
        #gameset[numgame]['game_workers_decisions'][workernum]['rounds']=rounds
      if roundnum not in gameset[numgame]['game_workers_decisions'][workernum] :
        gameset[numgame]['game_workers_decisions'][workernum][roundnum]=dict()
        if(tab_imageid[row['imageid']]['imageid']!=row['imageid']):
          gameset[numgame]['game_workers_decisions'][workernum][roundnum]['decisiontime']=gameset[tab_imageid[row['imageid']]['numgame']]['game_workers_decisions'][workernum][roundnum]['decisiontime']
        else :
          gameset[numgame]['game_workers_decisions'][workernum][roundnum]['decisiontime']=row['decisiontime']
        gameset[numgame]['game_workers_decisions'][workernum][roundnum]['decisions']=dict()
      if decisionnum not in gameset[numgame]['game_workers_decisions'][workernum][roundnum]['decisions']:
        imageid=row['imageid']
        imageid_to_copy=tab_imageid[imageid]['imageid']
        if(imageid!=imageid_to_copy):# redundant
          gameset[numgame]['game_workers_decisions'][workernum][roundnum]['decisions'][decisionnum]=gameset[tab_imageid[imageid_to_copy]['numgame']]['game_workers_decisions'][workernum][roundnum]['decisions'][tab_imageid[imageid_to_copy]['numcolumn']-1]
          # 20150502 : redundant images
          tab_of_redundant_images[str(numgame)+'#'+str(roundnum)+'#'+str(decisionnum)]=str(tab_imageid[imageid_to_copy]['numgame'])+'#'+str(roundnum)+'#'+str(tab_imageid[imageid_to_copy]['numcolumn']-1);
        else:
          gameset[numgame]['game_workers_decisions'][workernum][roundnum]['decisions'][decisionnum]=row['decisionvalue']
      #print imageid,numgame,workernum,roundnum,decisionnum,row['decisionvalue']
  db_session.commit()# required before returning in wsgi !!!
  content['games']=gameset
  content['tab_of_redundant_images']=tab_of_redundant_images
  return content
  
def db_get_decision(datebegin,dateend):
  content=dict()
  where_clause=""
  if(datebegin!=''):
    if(dateend!=''):
      where_clause=" AND SUBSTRING(gamesets.starttime,1,10)<="+GetSQLValueString(dateend, 'text')+\
                     " AND SUBSTRING(gamesets.starttime,1,10)>="+GetSQLValueString(datebegin, 'text')  
    else :
      where_clause=" AND SUBSTRING(gamesets.starttime,1,10)="+GetSQLValueString(datebegin, 'text')
  query= "SELECT gamesets.id AS gameset_id, games.id AS game_id,games.num as game_num, rounds.id AS round_id,rounds.num as round_num,  decisions.num AS decision_num, image.id AS image_id,"+\
            " image.pic_name AS pic_name, image.complexity AS image_complexity, image.color AS image_color, image.percent AS image_percent,"+\
            " choices.workerId AS workerId,decisions.value AS decision_value,decisions.reward AS decision_reward,decisions.status AS decision_status"+\
            " FROM gamesets, games, rounds, choices, decisions, image "+\
            " WHERE gamesets.id = games.gamesetid"+\
            " AND games.id = rounds.gameid"+\
            " AND rounds.id = choices.roundid "+\
            " AND choices.id = decisions.choiceid"+\
            " AND decisions.imageid = image.id "+\
            where_clause+\
            " ORDER BY gamesets.id,game_num,round_num,decision_num,workerId"
  #print query
  cursor.execute(query)
  rows=cursor.fetchall()

  i=1
  content[i]=(( 'gameset_id','game_id','game_num','round_id','round_num','decision_num','image_id','pic_name','image_complexity','image_color','image_percent',\
                            'workerId','decision_value','decision_reward','decision_status'))
  i=2
  for row in rows:
    content[i]=row
    i=i+1
  
  result=""
  for line in content:
    first=True
    for field in content[line]:
      value=str(field)
      value=value.replace(chr(13), " ")
      value=value.replace(chr(10), " ")
      value=value.replace(chr(9), " ")
      if first:
        result=result+value
      else:
        result=result+'\t'+value
      first=False  
    result=result+'\n'
  return result

def db_get_user(datebegin,dateend):
  result=''
  lastgamesetstarttime_user=dict()
  where_clause=""
  if(datebegin!=''):
    if(dateend!=''):
      where_clause=" AND SUBSTRING(gamesets.starttime,1,10)<="+GetSQLValueString(dateend, 'text')+\
                     " AND SUBSTRING(gamesets.starttime,1,10)>="+GetSQLValueString(datebegin, 'text')  
    else :
      where_clause=" AND SUBSTRING(gamesets.starttime,1,10)="+GetSQLValueString(datebegin, 'text')
  query= " select max(gamesets.starttime) as lastgamesettime,workerId as userid from gamesets, participants"+\
            " where gamesets.id=participants.gamesetid"+\
            where_clause+\
            " group by workerId"
  cursor.execute(query)
  rows=cursor.fetchall()
  for row in rows:
    lastgamesetstarttime_user[row['userid']]=row['lastgamesettime']
  
  query= " SELECT questionnaires.userid AS userid,users.username, users.email AS email,users.note,ipaddress,if(totalreward IS NULL,'',totalreward) as totalreward,enterQtime,leaveQtime,extraverted,"+\
            " critical, dependable, anxious, open, reserved, sympathetic, disorganized, calm,conventional, sexe, nativespeakenglish,schoolgrade"+\
            " FROM users "+\
            " INNER JOIN questionnaires ON users.id=questionnaires.userid"+\
            " INNER JOIN keycode_gameset_user ON  users.id=keycode_gameset_user.userid"+\
            " ORDER BY userid"
  cursor.execute(query)
  rows=cursor.fetchall()
  result=result+'userid'+'\t'+'username'+'\t'+'email'+'\t'+'note'+'\t'+'ipaddress'+'\t'+'totalreward'+'\t'+'enterQtime'+'\t'+'leaveQtime'+'\t'+'extraverted'+'\t'+'critical'+'\t'+'dependable'+'\t'+'anxious'+'\t'+'open'+'\t'+'reserved'+'\t'+'sympathetic'+'\t'+'disorganized'+'\t'+\
                            'calm'+'\t'+'conventional'+'\t'+'sexe'+'\t'+'nativespeakenglish'+'\t'+'schoolgrade'+'\t'+'last gameset time'+'\n'
  for row in rows:
    if str(row['userid']) in lastgamesetstarttime_user:
      first=True
      for field in row:
        value=str(field)
        value=value.replace(chr(13), " ")
        value=value.replace(chr(10), " ")
        value=value.replace(chr(9), " ")
        if first:
          result=result+value
        else:
          result=result+'\t'+value
        first=False
      result=result+'\t'+str(lastgamesetstarttime_user[str(row['userid'])])
      result=result+'\n'
  return result

def serious_workers_have_chosen(gameset,curgame,curround,EGParameters):
  # In order to don't disturb participants who are playing "seriously", we don't wait for answers of participants who didn't send a decision in the two
  # previous rounds.
  # To be considered as a "serious" participant again, a "non serious" participant has to send its answers before the last "serious" participant in the current round
  # If this participant is the "last serious one" for which we are waiting for, we will register choices of "non serious"
  # participants in the current round and go to the next one
  # Here we will know if all_serious_workers_have_chosen : if true the round will be terminated as if remaining time was out of limit below
  # select participants who answered automatically in the 2 previous rounds :
  if(len(curround.choices)>=1):
    curchoices = curround.choices
    serious_workers_in_2_previous_rounds=[]
    gamesetid=gameset.id
    gamenum=curgame.num
    roundnum=curround.num
    numroundmax=EGParameters['numRounds']
    if((gamenum==1 and roundnum>2) or (gamenum>1)):
      if(roundnum>2):
        roundnum_previous=roundnum-1
        gamenum_previous=gamenum
        roundnum_previous_previous=roundnum-2
        gamenum_previous_previous=gamenum
      elif(roundnum==2):
        roundnum_previous=roundnum-1
        gamenum_previous=gamenum
        roundnum_previous_previous=numroundmax
        gamenum_previous_previous=gamenum-1
      elif(roundnum==1):
        roundnum_previous=numroundmax
        gamenum_previous=gamenum-1
        roundnum_previous_previous=numroundmax-1
        gamenum_previous_previous=gamenum-1
      #games.id,games.num,rounds.id,rounds.num,choices.workerId,choices.id,decisions.id,decisions.status
      # workers who had, at least, one not AUTO decision in the 2 previous rounds: sumstatus=sum of status (1 or 2) is not max (max:all status=2) 
      query="select choices.workerId, sum(decisions.status) as sumstatus"+\
                " from games,rounds,choices,decisions"+\
                " where games.id=rounds.gameid and rounds.id=choices.roundid"+\
                " and choices.id=decisions.choiceid"+\
                " and ((games.num="+str(gamenum_previous)+" and rounds.num="+str(roundnum_previous)+") or (games.num="+str(gamenum_previous_previous)+" and rounds.num="+str(roundnum_previous_previous)+"))"+\
                " and games.gamesetid="+str(gamesetid)+\
                " group by workerId"+\
                " order by 0+choices.workerId";
      cursor.execute(query)
      rows=cursor.fetchall()
      for row in rows:
        a_workerId=row[workerId]
        sumstatus=int(row[sumstatus])
        if(sumstatus!=2*2*EGParameters['columnNumber']):#2 for status.AUTO, 2 for 2 last rounds, columnNumber=decisionNumber. If at least one decision during previous 2 rounds was not AUTO
          serious_workers_in_2_previous_rounds.append(a_workerId)
      workerIdListInCurrentChoice=[]
      for a_choice in curchoices:
        workerIdListInCurrentChoice.append(a_choice.workerId)
      all_serious_workers_have_chosen=True
      for a_serious_workerId in serious_workers_in_2_previous_rounds:
        a_serious_worker_has_chosen=False
        for a_workerIdInCurrentChoice in workerIdListInCurrentChoice:
            if a_serious_workerId == a_workerIdInCurrentChoice:
              a_serious_worker_has_chosen=True
        all_serious_workers_have_chosen=all_serious_workers_have_chosen and a_serious_worker_has_chosen
  return all_serious_workers_have_chosen


def pay_participants(EGParameters):
  # curl -k -X POST --data-urlencode "amount=1" https://api.crowdflower.com/v1/jobs/930744/workers/21619284/bonus.json?key=vir74DJsY4m5Jz6BwcM-
  # {"success":{"message":"Bonus of $0.01 rewarded"}} or {"error": {"message":"We couldn't find what you were looking for."}}
  pay_result=dict()
  # Send a bonus
  query= "select keyCodeBegin, keyCodeEnd, users.username as cwf_contributor_id,"+\
            " keycode_gameset_user.status, keycode_gameset_user.bonus"+\
            " from keycode_gameset_user,users,gamesets"+\
            " where keycode_gameset_user.userid=users.id"+\
            " and keycode_gameset_user.gamesetid=gamesets.id"+\
            " and gamesets.job_id='"+EGParameters['job_id']+"'"+\
            " and keycode_gameset_user.status='USED'"+\
            " order by keycode_gameset_user.gamesetid,users.username asc"
  cursor.execute(query)
  rows=cursor.fetchall()
  for row in rows:
    cwf_contributor_id = row['cwf_contributor_id']
    pay_result[cwf_contributor_id]=dict()
    pay_result[cwf_contributor_id]['resultpaycode']=''
    pay_result[cwf_contributor_id]['resultpaymessage']=''
    if cwf_contributor_id.isdigit():
      bonus=row['bonus']
      if int((float("0"+bonus)*100))>0:
        if int((float("0"+bonus)*100))<=int((float(EGParameters['bonusmax'])*100)):
          amount = str(int((float("0"+bonus)*100)))# converts dollars to cents
          if EGParameters['pay_platform']=='cwf':
            #cmd_bonus = "curl -k -X POST --data-urlencode \"amount=" + amount + "\" https://api.crowdflower.com/v1/jobs/"+EGParameters['job_id']+"/workers/"+cwf_contributor_id+"/bonus.json?key="+EGParameters['cwf_api_key']
            cmd_bonus=['curl','-X', 'POST', '--data-urlencode', 'amount='+amount,'https://api.crowdflower.com/v1/jobs/'+EGParameters['job_id']+'/workers/'+cwf_contributor_id+'/bonus.json?key='+EGParameters['cwf_api_key']]
          else:
            #cmd_bonus = "curl -k -X POST --data-urlencode \"amount=" + amount + "\" http://localhost/tests/reponse_wsgi.php"
            cmd_bonus=['curl','-X', 'POST', '--data-urlencode', 'amount='+amount,'http://localhost/tests/reponse_wsgi.php']
          print cmd_bonus
          # outfile = open(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+'/tmp/'+cwf_contributor_id)), 'w');
          # status = subprocess.Popen(cmd_bonus, bufsize=0, stdout=outfile)
          # outfile.close()
          # infile = open(os.path.normpath(os.path.abspath(os.path.dirname(__file__)+'/tmp/'+cwf_contributor_id)), 'r');
          # timedeb = datetime.utcnow()
          # resultpaymessage=''
          # cwf_timeout=False
          # while resultpaymessage=='' and not cwf_timeout:
            # resultpaymessage=infile.read()
            # cwf_timeout=(datetime.utcnow()-timedeb).total_seconds()>EGParameters['cwf_timeout']
          # infile.close()
          cwf_timeout=False
          resultpaymessage = subprocess.check_output(cmd_bonus)
          print 'resultpaymessage : '+resultpaymessage
          if not cwf_timeout:
            pay_result[cwf_contributor_id]['resultpaymessage']=resultpaymessage
            if pay_result[cwf_contributor_id]['resultpaymessage'].find("success")!=-1 :#error success[2:7]
              pay_result[cwf_contributor_id]['resultpaycode']='AUTO_PAID'
              query="update keycode_gameset_user set status='PAID',paidtime='"+str(datetime.now())+"'"+\
                        ",cwf_contributor_id="+GetSQLValueString(cwf_contributor_id, "text")+\
                        ",resultpaycode="+GetSQLValueString(pay_result[cwf_contributor_id]['resultpaycode'], "text")+\
                        ",resultpaymessage="+GetSQLValueString(pay_result[cwf_contributor_id]['resultpaycode'], "text")+\
                        " where keyCodeBegin='"+row['keyCodeBegin']+"'"
              cursor.execute(query)
              connection.commit()
            else :
              pay_result[cwf_contributor_id]['resultpaycode']='ERROR'
          else:
            pay_result[cwf_contributor_id]['resultpaycode']='WARNING'
            pay_result[cwf_contributor_id]['resultpaymessage']="time out "+str(EGParameters['cwf_timeout'])+"s"
        else:
          pay_result[cwf_contributor_id]['resultpaycode']='WARNING'
          pay_result[cwf_contributor_id]['resultpaymessage']="nothing paid : bonus exceeded $"+EGParameters['bonusmax']
      else:
        pay_result[cwf_contributor_id]['resultpaycode']='INFO'
        pay_result[cwf_contributor_id]['resultpaymessage']="nothing to pay : 0" 
    else:
      pay_result[cwf_contributor_id]['resultpaycode']='WARNING'
      pay_result[cwf_contributor_id]['resultpaymessage']='cwf_contributor_id contains at least one non-digit character'
    
    if pay_result[cwf_contributor_id]['resultpaycode']!='PAID':
      query="update keycode_gameset_user set cwf_contributor_id="+GetSQLValueString(cwf_contributor_id, "text")+\
                ",resultpaycode="+GetSQLValueString(pay_result[cwf_contributor_id]['resultpaycode'], "text")+\
                ",resultpaymessage="+GetSQLValueString(pay_result[cwf_contributor_id]['resultpaymessage'], "text")+\
                " where keyCodeBegin='"+row['keyCodeBegin']+"'"
      cursor.execute(query)
      connection.commit()
    print "pay_result[cwf_contributor_id]['resultpaycode']"+pay_result[cwf_contributor_id]['resultpaycode']
    
    
def view_participants_of_a_job_id(EGParameters):
  content=dict()
  query= "select  users.username as cwf_contributor_id, users.lastvisit, gamesets.id, participant_statuslib as partstatus,"+\
            " keyCodeBegin,keycode_gameset_user.status as key_code_status, keycode_gameset_user.bonus,"+\
            " if(resultpaycode IS NULL,'',resultpaycode) as resultpaycode,if(resultpaymessage IS NULL,'',resultpaymessage) as resultpaymessage"+\
            " from keycode_gameset_user,users,gamesets,participants,participant_status"+\
            " where keycode_gameset_user.userid=users.id"+\
            " and users.id=0+participants.workerId"+\
            " and participants.status=participant_status.participant_statuscode"+\
            " and keycode_gameset_user.gamesetid=gamesets.id"+\
            " and gamesets.job_id='"+EGParameters['job_id']+"'"+\
            " order by keycode_gameset_user.gamesetid,users.username asc"
  cursor_without_keys.execute(query)
  rows=cursor_without_keys.fetchall()
  i=0
  content[i]=("cwf_contributor_id","lastvisit","gameset","part status","key code","key code status","bonus","resultpaycode","resultpaymessage")
  for row in rows:
    i=i+1
    content[i]=row
  return content
