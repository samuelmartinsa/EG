#!python
from flask import abort, send_file
from datetime import datetime, timedelta
import string
import time
import sys
import argparse
import os
import csv
import json
import logging
import traceback
import site
import random
from string import split
from distutils.sysconfig import get_python_lib
from functools import wraps
from sqlalchemy import or_
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.expression import cast 
from sqlalchemy import distinct
from flask import Flask, render_template, request, Response, make_response, has_request_context
from werkzeug.datastructures import MultiDict # for access to request.values.has_key
from numpy import median
import subprocess
import tempfile

# our classes
from fractale_complex import fractale_complex
from peanuts_light import peanuts_light
from create_gameset_picture import create_gameset_picture
# Database setup : our db and models classes
from db import db_session, init_db,free_images,generateNewKeyCodes,connection,engine,serious_workers_have_chosen,\
                get_db_keys_users_gamesets,db_get_free_keys, get_db_users_gamesets,db_get_decision,db_get_user,\
                clean_tables_after_end_on_start,GetSQLValueString,get_EG_session_info,dump_db,\
                select_and_create_games, check_for_enough_games, pay_participants, view_participants_of_a_job_id
from models import Participant, Game, GameSet, Round, Choice, Decision, User, Questionnaire, Code, Image,keycode_gameset_user
# our config class
from config import config

application = app = Flask(__name__)

logfilepath = os.path.join(os.path.dirname(os.path.abspath(__file__)),config.get("Server Parameters", "logfile"))
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
loglevel = loglevels[config.getint('Server Parameters', 'loglevel')]
logging.basicConfig( filename=logfilepath, format='%(asctime)s %(message)s', level=loglevel )
phpPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),config.get("Server Parameters", "phpPath"))

SERVER_HOST = config.get('Server Parameters', 'host')
SERVER_PORT = config.getint('Server Parameters', 'port')
SERVER_DEBUG = config.getboolean('Server Parameters', 'debug')
DATABASE_NAME=config.get('Database Parameters', 'database_name')    
#----------------------------------------------
# ExperimentError Exception, for db errors, etc.
#----------------------------------------------
# Possible ExperimentError values.
experiment_errors = dict(
    status_incorrectly_set = 1000, 
    hit_assign_worker_id_not_set_in_mturk = 1001,
    hit_assign_worker_id_not_set_in_consent = 1002,
    hit_assign_worker_id_not_set_in_instruct = 1003,
    hit_assign_appears_in_database_more_than_once = 1004,
    user_already_in_game = 1005,
    wrong_status_in_redirect = 1006,
    user_appears_in_database_more_than_once = 1007,    
    already_started_exp = 1008,    
    already_started_exp_mturk = 1009,
    already_did_exp_hit = 1010,
    tried_to_quit= 1011,
    intermediate_save = 1012,
    improper_inputs = 1013,
    hit_assign_worker_id_not_set_in_waitingroom = 1014,
    game_not_assigned_to_participant_in_waitingroom = 1015,
    hit_assign_worker_id_not_set_in_exp = 1016,
    sessionId_not_set_in_consent = 1017,
    user_in_db_more_than_once = 1018,
    sessionId_not_set = 1019,
    hit_assign_worker_id_not_set = 1020,
    part_has_more_than_one_started_game = 1021,
    participant_not_found_gameset_exists_waiting_room = 1022,
    improper_inputs_in_questionnaire = 1023,
    too_many_participants=1024,
    user_has_more_than_one_gameset_not_terminated_and_keycode_in_use=1025,
    user_has_0_or_more_than_1_keycode_in_use=1026,
    game_not_found_for_gameset_not_terminated=1027,
    not_enough_images_for_the_gameset = 1028,
    hit_assign_does_not_appear_in_database = 1029,
    page_not_found = 404,
    in_debug = 2005,
    insuffisant_image_number=5000,#>=5000 : error due to an inextricable situation
    unknown_error = 9999
)

class ExperimentError(Exception):#,data_to_logError class for experimental errors, such as subject not being found in the database.
    def __init__(self, value):
        self.value = value
        self.errornum = experiment_errors[self.value]
    def __str__(self):
        return repr(self.value)
    def error_page(self, request):
        try:
          sql="insert into errorlog (data_to_log) values()"
        except:
          print "Exception on insert into errolog",self.errornum 
        return render_template('/eg/error.html',errornum=self.errornum,EGParameters=EGParameters,**request.args)

@app.errorhandler(ExperimentError)
def handleExpError(e):#Handle errors by sending an error page.
    return e.error_page( request )

#----------------------------------------------
# DB setup
#----------------------------------------------
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()

#----------------------------------------------
# general utilities
#----------------------------------------------
def dump_py_obj(obj):
  for attr in dir(obj):
    print "obj.%s = %s" % (attr, getattr(obj, attr))
  return


#----------------------------------------------
# routes
#----------------------------------------------

def check_session(user,session):
    #print "in check_session user.id ",user.id,"user.sessionId ",user.sessionId,"now()",datetime.now() 
    if(user.sessionId!=session or not user.lastvisit or (datetime.now() - user.lastvisit) > timedelta (minutes = 10)):         
        return False;
    else:
        user.lastvisit = datetime.now(); # update
        return True;

@app.route('/eg/login', methods=['GET','POST'])
def give_login():
  global EGParameters
  
  # added for robot
  if(request.args.has_key('robot') and request.args['robot']=='askforuserkeycode'):
    robotValues=robot_create();
    return robotValues
  # end added for robot
  
  # 11/03/2015 if user already has a sessionId, redirect him in the good way
  if request.args.has_key('hitId') and request.args.has_key('assignmentId') and request.args.has_key('workerId')\
            and request.args['hitId']!='' and request.args['assignmentId']!='' and request.args['workerId']!='':
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request)
    if to_return==None:
      return redirect(user,hitId,assignmentId,workerId,user.sessionId)
  # end 11/03/2015
  
  loginValues={'keyCodeBegin':'','username':'','loginsignin':'new','pwd':'','pwd2':''};
  nowDate = datetime.utcnow()
  #nextGameDate = nowDate.replace(hour=int(list(split(EGParameters['starthour'],':'))[0]), minute=int(list(split(EGParameters['starthour'],':'))[1]), second=0 , microsecond =0)
  query_rs_keyCode=""
  rs_keyCode=None
  row_rs_keyCode=None
  givenKeyCodeBegin="";
  userId_of_givenKeyCodeBegin=-1
  gameSetId_of_givenCodeKeyCodeBegin=-1
  flag=""
  ipaddress = None#request.remote_addr;
  # if a proxy server in front of the application
  if request.environ.get('HTTP_X_FORWARDED_FOR'):
    ipaddress=request.environ['HTTP_X_FORWARDED_FOR']
    #print 'HTTP_X_FORWARDED_FOR',ipaddress
  elif request.environ.get('REMOTE_ADDR'):
    ipaddress=request.environ['REMOTE_ADDR']
  #print ipaddress
  timeLeft=0
  loginState=''
  timerValue=(nowDate-EGParameters['nextGameDate']).total_seconds()
  if(timerValue<0):
    loginState='beforeLogin'
    timeLeft=abs(int(timerValue))
  else:
    loginState='openLogin'
    timeLeft=abs(int(timerValue)-EGParameters['maxDelayToLoginGameSet']*60)
    if(timerValue-EGParameters['maxDelayToLoginGameSet']*60>0):
      loginState='closeLogin'
      timeLeft=0
  loginAttributes={'EGRunning':EGParameters['EGRunning'],
              'activateTimer':EGParameters['activateTimer'],
              'loginState':loginState,
              'timeLeft':str((timeLeft)//60)+'mn '+str((timeLeft)%60),
              'keyCodeMode':EGParameters['keyCodeMode']
             }
  
  if(request.method == "POST"):
    # fill loginValues table with posted values
    for key in loginValues:
      if request.form.has_key(key):
        loginValues[key]=string.strip(request.form[key])
    ## end for
    if(EGParameters['activateTimer']=='y' and loginState!='openLogin'):# disable login
        return render_template('/eg/login.html',flag="LOGIN_NOT_OPEN",loginValues=loginValues, EGParameters=EGParameters);
    ## end if
    if(EGParameters['keyCodeMode']=='y'):
      if(request.form.has_key('keyCodeBegin')):
        givenKeyCodeBegin=string.strip(request.form['keyCodeBegin']);
        # check if keycode exists and is not in a terminated gameset (unused, waiting_for_participants or started)
        query_rs_keyCode="select count(*) as count from keycode_gameset_user"+\
                          " where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text")+\
                          " and keycode_gameset_user.gamesetid not in (select id from gamesets where status=3)"
        rs_keyCode=engine.execute(query_rs_keyCode)
        row_rs_keyCode=rs_keyCode.fetchone()
        if(row_rs_keyCode['count']==1) :
          query_rs_keyCode="select * from keycode_gameset_user where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text")
          rs_keyCode=engine.execute(query_rs_keyCode)
          row_rs_keyCode=rs_keyCode.fetchone()
          userId_of_givenKeyCodeBegin=row_rs_keyCode['userid']
          gameSetId_of_givenCodeKeyCodeBegin=row_rs_keyCode['gamesetid']
        else:
          return render_template('/eg/login.html',flag="KEYCODE_NONEXISTANT_OR_USED",loginValues=loginValues,EGParameters=EGParameters);
      # no key code required : automaticaly assigned to the user 
      # elif ((EGParameters['useExistingGames']=='y' and not request.form.has_key('keyCodeBegin'))) or EGParameters['skipConsentInstruct']=='y':
      # givenKeyCodeBegin=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
      # 23032015 else
      else:
        return render_template('/eg/login.html',flag="MISSING_KEYCODE",loginValues=loginValues,EGParameters=EGParameters);
    
    # key code exists in db and is not used in a terminated gameset
    # and (EGParameters['activateTimer']=='n' or loginState=='openLogin')
    # users and robots have to login :
    # - a user requests with 'loginsignin'="new" or "returning"
    # - a robot requests with  'loginsignin'="robot" : ip and keycode are not checked 
    if(request.form.has_key('username') and request.form.has_key('pwd') and request.form.has_key('loginsignin')):
      query="select count(*) as count from users where ipaddress='"+ipaddress+"'"# and ip_in_use='y'"
      rs=engine.execute(query)
      row_rs=rs.fetchone()
      if row_rs['count']>=1 and EGParameters['checkIP']=='y':
        return render_template('/eg/login.html',imageType=EGParameters['imageType'],flag="IP_ALREADY_IN_DB",loginValues=loginValues,EGParameters=EGParameters);

      username = request.form['username'];
      password = request.form['pwd']
      if(request.form['loginsignin']=="new"):
        # Check if username exists in database
        # 1
        matchesUser = User.query.filter(User.username == username).all();
        if(len(matchesUser)==1):
          return render_template('/eg/login.html',flag="ALREADY_IN_DB",loginValues=loginValues,EGParameters=EGParameters);
        elif(len(matchesUser)==0):
          # check for existing IP address (this feature does not work yet because IP is not properly fetch and put in database)
          if(EGParameters['checkIP']=='y'):
            # 2
            matchesIP = User.query.filter(User.ipaddress == ipaddress).filter(User.ip_in_use=='y').all();
            if(len(matchesIP)>=1):
              return render_template('/eg/login.html',imageType=EGParameters['imageType'],flag="IP_ALREADY_IN_DB",loginValues=loginValues,EGParameters=EGParameters);
          # end if
          # 23032015
          if(userId_of_givenKeyCodeBegin!=-1 and EGParameters['keyCodeMode']=='y'): #already assigned to an other user
            return render_template('/eg/login.html',flag="KEYCODE_ALREADY_USED",loginValues=loginValues,EGParameters=EGParameters);
          # 3
          user = NewUser(username,password,ipaddress)#
          user.ip_in_use='y'
          db_session.add(user)
          db_session.commit()
          workerId = str(user.id);
          # if EGParameters['useExistingGames']=='y' and not request.form.has_key('keyCodeBegin'):# no key code required in useExistingGames mode: create 
            # creationtime=str(datetime.now())
            # query="insert into keycode_gameset_user (keyCodeBegin,creationtime,usagetime,userid,gamesetid,keyCodeEnd,status) values ('"+givenKeyCodeBegin+"','"+creationtime+"','"+str(datetime.now())+"',-1,-1,'','')"
            # engine.execute(query)
          # 23032015
          if EGParameters['keyCodeMode']=='y':
            engine.execute("update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE', usagetime='"+str(datetime.now())+"' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text"))
          assignmentId = "0";
          hitId = "0";
          return render_template('/eg/consent.html',sessionId=user.sessionId, hitId = hitId, assignmentId=assignmentId, workerId=workerId,EGParameters=EGParameters);
        else:
          print "Error, user appears in database more than once (serious problem)"
          raise ExperimentError( 'user_appears_in_database_more_than_once' )
        ## end if
      elif(request.form['loginsignin']=="returning"): # user already exists in db
        if(EGParameters['withPassword']=='n'):
          return render_template('/eg/login.html',flag="APOLOGIES_NORETURN",loginValues=loginValues,EGParameters=EGParameters);
        else:
          # 4
          matchesUser = User.query.filter(User.username == username).filter(User.password == password).all();
          if(len(matchesUser)==0):# user/password doesn't exist in db
            return render_template('/eg/login.html',flag="AUTH_FAILED",loginValues=loginValues,EGParameters=EGParameters);
          elif(len(matchesUser)==1):
            user = matchesUser[0];
            # Gameset running for this user ?
            # 23032015 : keyCodeMode check
            if EGParameters['keyCodeMode']=='y':
              query_rs_keyCode="select count(*) as count from keycode_gameset_user, gamesets"+\
                               " where userid="+str(user.id)+" and keycode_gameset_user.gamesetid=gamesets.id"+\
                               " and gamesets.status<>3 and keycode_gameset_user.status='IN_USE'"
              rs_keyCode=engine.execute(query_rs_keyCode)
              row_rs_keyCode=rs_keyCode.fetchone()
              gameset_running_for_user=False
              if(row_rs_keyCode['count']>1):
                raise ExperimentError( 'user_has_more_than_one_gameset_not_terminated_and_keycode_in_use' )
              elif(row_rs_keyCode['count']==1):
                gameset_running_for_user=True
                query_rs_keyCode="select * from keycode_gameset_user, gamesets"+\
                                 " where userid="+str(user.id)+" and keycode_gameset_user.gamesetid=gamesets.id"+\
                                 " and gamesets.status<>3 and keycode_gameset_user.status='IN_USE'"
                rs_keyCode=engine.execute(query_rs_keyCode)
                row_rs_keyCode=rs_keyCode.fetchone()
              if(userId_of_givenKeyCodeBegin==-1):
                if(gameset_running_for_user): # gameset running (status=<>3) for the user
                  return render_template('/eg/login.html',flag="KEYCODE_GIVEN_WHILE_ANOTHER_IN_USE_FOR_A_NON_TERMINATED_GAMESET",loginValues=loginValues,EGParameters=EGParameters);
                else:
                  #print "update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text")
                  engine.execute("update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE', usagetime='"+str(datetime.now())+"' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text"))
              else:
                if(userId_of_givenKeyCodeBegin==user.id):
                  print 'returning user in its gameset : ',gameSetId_of_givenCodeKeyCodeBegin
                else:
                  return render_template('/eg/login.html',flag="KEYCODE_ALREADY_USED",loginValues=loginValues,EGParameters=EGParameters);
            user.ipaddress = ipaddress
            user.lastvisit = datetime.now();
            user.sessionId = random.randint(10000000, 99999999);
            # 5
            db_session.add(user)
            db_session.commit()
            workerId = str(user.id);
            assignmentId = "0";
            hitId = "0";
            #print "user found", user.username
            return render_template('/eg/consent.html',sessionId=user.sessionId, hitId = hitId, assignmentId=assignmentId, workerId=workerId,EGParameters=EGParameters);
          else:
            print "Error, user appears in database more than once (serious problem)"
            raise ExperimentError( 'user_appears_in_database_more_than_once' )
      # end elif(request.form['loginsignin']=="returning")
      # added for robot
      elif(request.form['loginsignin']=="robot"):
        # 6
        matchesUser = User.query.filter(User.username == username).filter(User.password == password).all();
        user = matchesUser[0];
        user.ipaddress = ipaddress
        user.ip_in_use='n'
        user.lastvisit = datetime.now();
        user.sessionId = random.randint(10000000, 99999999);
        db_session.add(user)
        db_session.commit()
        workerId = str(user.id);
        assignmentId = "0";
        hitId = "0";
        if EGParameters['skipConsentInstruct']=='y' :
          user.status=User.INSTRUCTED
          # 7
          db_session.add(user)
          db_session.commit()
          return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=user.sessionId,gameset_pic_name="",EGParameters=EGParameters) 
        else:
          return render_template('/eg/consent.html',sessionId=user.sessionId, hitId = hitId, assignmentId=assignmentId, workerId=workerId,EGParameters=EGParameters);
      # end added for robot 
    else:
      return render_template('/eg/login.html',flag="MISSING_USERNAME_OR_PWD",loginValues=loginValues,EGParameters=EGParameters);
    # end if(request.form.has_key('username') and request.form.has_key('pwd') and request.form.has_key('loginsignin'))
  # end if "POST"
  if(request.args.has_key('flag')):
    flag = request.args['flag'];
  else:
    flag = "";
  # getFlag to display (or not) status, time left and login form fields
  if(request.args.has_key('getFlag')):
    return json.dumps(loginAttributes)
  else:
    return render_template('/eg/login.html', flag=flag,loginValues=loginValues,EGParameters=EGParameters)

# added for robot : create user, keycode with status='IN_USE' 
def robot_create():
  duplicate_primarykey=True # sometimes 2 KC are generated at the same time ? try until different
  while duplicate_primarykey:
    timesuffix=str(datetime.now())
    username='robot'+timesuffix
    robotuser=NewUser(username,'','')
    robotkeycode='KCrobot'+timesuffix
    query="insert into keycode_gameset_user (keyCodeBegin,creationtime,usagetime,userid,gamesetid,keyCodeEnd,status) values ('"+robotkeycode+"','"+timesuffix+"','"+timesuffix+"',"+str(robotuser.id)+",-1,'"+str(random.randint(10000000, 99999999))+"','IN_USE')"
    try:
      engine.execute(query)
      duplicate_primarykey=False
    except:
      duplicate_primarykey=True
  return json.dumps({'keyCodeBegin':robotkeycode,'username':username,'loginsignin':'robot','pwd':'','pwd2':'','skipConsentInstruct':EGParameters['skipConsentInstruct']});
# end added for robot 

def NewUser(username,password,ipaddress):#
  user = User();
  user.username = username;
  user.password = password;
  user.ipaddress=ipaddress
  user.lastvisit = datetime.now();
  user.sessionId = random.randint(10000000, 99999999);
  # 8
  db_session.add(user)
  db_session.commit()
  return user
    
def check_identity(request):
    loginValues={'keyCodeBegin':'','username':'','loginsignin':'','pwd':'','pwd2':''};    
    if not (request.args.has_key('hitId') and request.args.has_key('assignmentId') and request.args.has_key('workerId')):
        raise ExperimentError('hit_assign_worker_id_not_set')
    hitId = request.args['hitId']
    assignmentId = request.args['assignmentId']
    workerId = request.args['workerId']
    to_return = None;
    
    if not request.args.has_key('sessionId'):
        raise  ExperimentError('sessionId_not_set')
    # 9
    matches = User.query.filter(User.id == int(workerId)).all();
    if(len(matches)==0):
        to_return = render_template('/eg/login.html',flag="SESSION_EXPIRED",loginValues=loginValues,EGParameters=EGParameters);                       
        return [hitId,assignmentId,workerId,None,to_return]
    elif(len(matches)>1):
        print "User in db more than once, serious trouble"
        raise  ExperimentError('user_in_db_more_than_once')
    user = matches[0];
    session = request.args['sessionId'];
    if(not check_session(user,session)):
        #to_return = render_template('/eg/login.html',flag="SESSION_EXPIRED",loginValues=loginValues,EGParameters=EGParameters);        
        to_return=render_template('/eg/session_has_expired.html');        
    return [hitId,assignmentId,workerId,user,to_return]

@app.route('/eg/consent', methods=['GET','POST'])
def give_consent():      
    if not EGParameters['EGRunning']:
      return render_template('/eg/login.html',flag="LOGIN_NOT_OPEN",loginValues={'keyCodeBegin':'','username':'','loginsignin':'','pwd':'','pwd2':''}, EGParameters=EGParameters);
    
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    hitId = 0;
    assignmentId = 0;
    if to_return!=None:
        return to_return;    
        
    if(request.method == "POST" and request.form.has_key('consented') and request.form['consented']):
        user.status = User.CONSENTED
        # 23032015
        if EGParameters['skipQuestionnaire']=='y':
          user.status = User.ASSESSED
        # 23032015
        # 10
        db_session.add(user)
        db_session.commit()
    
    res = redirect(user,hitId,assignmentId,workerId,user.sessionId)
    return res

def findParticipant(hitId,assignmentId,workerId,addIfNotFound):
    # 11
    matches = Participant.query.\
                        filter(Participant.hitId == hitId).\
                        filter(Participant.assignmentId == assignmentId).\
                        filter(Participant.workerId == workerId).\
                        all()
    numrecs = len(matches)
    if numrecs == 0:
        #print 'Participant not in database yet'
        if(addIfNotFound):
            # Choose condition and counterbalance, subj_cond, subj_counter = get_random_condcount()
            if not request.remote_addr:
                myip = "UKNOWNIP"
            else:
                myip = request.remote_addr
            # set condition here and insert into database
            part = Participant( hitId, myip, assignmentId, workerId, 0, 0)
            part.status = Participant.INSTRUCTED
            # 12
            db_session.add( part )
            db_session.commit()
            #print 'Participant added in database'
            return part
        else:
            return False
    elif numrecs == 1:
        # 13
        return matches[0]
    else:
        print "Error, hit/assignment appears in database more than once (serious problem)"
        raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )

def findUser(workerId):
    # 14
    matches = User.query.filter(User.id == int(workerId)).all()
    numrecs = len(matches)
    if numrecs == 0:
        #print 'User not in database yet'
        return False
    elif numrecs == 1:
        return matches[0]
    else:
        print "Error, hit/assignment appears in database more than once (serious problem)"
        raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )

def redirect(user,hitId,assignmentId,workerId,sessionId):
  # skipConsentInstruct for test : go directly to waitingroom to avoid firsts pages
  if not EGParameters['EGRunning']:
    return render_template('/eg/login.html',flag="LOGIN_NOT_OPEN",loginValues={'keyCodeBegin':'','username':'','loginsignin':'','pwd':'','pwd2':''}, EGParameters=EGParameters);
  
  if EGParameters['skipConsentInstruct']=='y' :
    user.status=User.INSTRUCTED
    # 15
    db_session.add(user)
    db_session.commit()
    #return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,gameset_pic_name="",EGParameters=EGParameters) 
    return wait_in_room()
  else :
    if(not user or user.status == User.ALLOCATED):
      return render_template('/eg/consent.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,EGParameters=EGParameters)
    elif(user.status == User.CONSENTED):
      return render_template('/eg/questionnaire_first.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,EGParameters=EGParameters)    
    elif(user.status == User.ASSESSED):
      return render_template('/eg/instruct.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,EGParameters=EGParameters) 
    elif(user.status == User.INSTRUCTED):
      # 11/03/2015
      addIfNotFound=False
      part = findParticipant(hitId,assignmentId,workerId,addIfNotFound)
      if not part:
        return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,gameset_pic_name="",EGParameters=EGParameters) 
      else:
        return start_exp_consensus(part)
      # end 11/03/2015
    else:
      print "Error in redirection"
      raise ExperimentError('user_already_in_game');       

@app.route('/eg/instruct', methods=['GET','POST'])
def give_instruct():
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:#print "returning to login"
      return to_return
    #print 'give_instruct ',hitId, assignmentId, workerId
    if(request.method == "POST" and request.form.has_key('instructed') and request.form['instructed']):
      user.status = User.INSTRUCTED
      # 16
      db_session.add(user)
      db_session.commit()
    
    return redirect(user,hitId,assignmentId,workerId,user.sessionId)

@app.route('/eg/exp', methods=['GET'])
def start_exp():
    if not (request.args.has_key('hitId') and request.args.has_key('assignmentId') and request.args.has_key('workerId')):
      raise ExperimentError( 'hit_assign_worker_id_not_set_in_exp' )
    hitId = request.args['hitId']
    assignmentId = request.args['assignmentId']
    workerId = request.args['workerId']
    #print 'start_exp ',hitId, assignmentId, workerId
    # check first to see if this hitId or assignmentId exists.  if so check to see if inExp is set
    # 17
    matches = Participant.query.\
                        filter(Participant.hitId == hitId).\
                        filter(Participant.assignmentId == assignmentId).\
                        filter(Participant.workerId == workerId).\
                        all()
    numrecs = len(matches)
    if numrecs == 0:
        # Choose condition and counterbalance, subj_cond, subj_counter = get_random_condcount()
        if not request.remote_addr:
            myip = "UKNOWNIP"
        else:
            myip = request.remote_addr
        # set condition here and insert into database
        # 18
        part = Participant( hitId, myip, assignmentId, workerId, 0, 0)
        db_session.add( part )
        db_session.commit()
    
    elif numrecs==1:
        part = matches[0]
        #if part.status>=Participant.STARTED: # in experiment (or later) can't restart at this point
        #    raise ExperimentError( 'already_started_exp' )
    else:
        print "Error, hit/assignment appears in database more than once (serious problem)"
        raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )
    
    return render_template('/eg/exp.html', workerId=part.workerId, assignmentId=part.assignmentId, cond=part.cond, counter=part.counterbalance,EGParameters=EGParameters )

@app.route('/eg/waitingroom', methods=['GET','POST'])
def wait_in_room():
    if not EGParameters['EGRunning']:
      if (request.args.has_key('getFlag')):
        return json.dumps({'status':'EG_NOT_RUNNING'})
      else:
        return render_template('/eg/login.html',flag="LOGIN_NOT_OPEN",loginValues={'keyCodeBegin':'','username':'','loginsignin':'','pwd':'','pwd2':''}, EGParameters=EGParameters);

    nowDate = datetime.utcnow()
    timerValue=(nowDate-EGParameters['nextGameDate']).total_seconds()
    if(timerValue<0):
      loginState='beforeLogin'
    else:
      loginState='openLogin'
      if(timerValue-EGParameters['maxDelayToLoginGameSet']*60>0):
        loginState='closeLogin'
      if(timerValue-EGParameters['maxDelayToBeginGameSet']*60>0):
        loginState='closeWait_in_room'
    leftDelayToBeginGameSet=abs(int(timerValue)-EGParameters['maxDelayToBeginGameSet']*60)
    
    # participant has to exit from the waiting room. Gamesets will be cancelled by administrator
    if request.args.has_key('getFlag'):
      if(EGParameters['activateTimer']=='y' and loginState=='closeWait_in_room'):
        return json.dumps({'status':'closeWait_in_room'})
    
    #print 'wait_in_room leftDelayToBeginGameSet',leftDelayToBeginGameSet
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:#print "returning to login"
        return to_return      
    
    if(user.status<=User.ALLOCATED):
        if (request.args.has_key('getFlag')):
            return json.dumps({'status':'USER_NOT_ALLOCATED'})#-2
        else:# Participant needs to consent and get the game instructions first
            return render_template('/eg/consent.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId = user.sessionId,EGParameters=EGParameters)     

    if(user.status<=User.CONSENTED):
        if (request.args.has_key('getFlag')):
            return json.dumps({'status':'USER_NOT_CONSENTED'})
            #-3
        else:            
            return render_template('/eg/instruct.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId = user.sessionId,EGParameters=EGParameters)    
    #print "Annoying query"
    # 19
    currentGamesets = GameSet.query.join(Participant.gamesets)\
                            .filter(Participant.workerId == str(user.id))\
                            .filter(GameSet.status!=GameSet.TERMINATED).all()
    if len(currentGamesets)== 0:# user not in a current gameset
        # assign a gameset to the participant        
        # 12092016 added by PG : filter(GameSet.status!=GameSet.TERMINATED).\
        vacantGameSets = db_session.query(GameSet.id,func.count(GameSet.id),GameSet.numExpectedParticipants,Participant.workerId,Participant.assignmentId).\
                                        join((Participant,GameSet.participants)).\
                                        filter(GameSet.status!=GameSet.TERMINATED).\
                                        group_by(GameSet.id).\
                                        having(func.count(GameSet.id)<GameSet.numExpectedParticipants)
        # 12092016 added by PG
        if EGParameters['addRobotsMode']=='y' and not request.args.has_key('robot') : # in addRobotsMode, a user (not robot) always create a new gameset
          number_of_vacantGameSets=0
        else :
          number_of_vacantGameSets=vacantGameSets.count()
        if(number_of_vacantGameSets==0 and not request.args.has_key('robot')):# a robot may not create a gameset
            # 20
            num_free_images=Image.query.filter(Image.status == Image.FREE,Image.pic_type==EGParameters['imageType']).count()
            if(num_free_images < EGParameters['numGames']*EGParameters['columnNumber'] and not EGParameters['useExistingGames']=='y' and not EGParameters['redundantMode']=='y'):
              raise ExperimentError('not_enough_images_for_the_gameset')
            gameset = GameSet();
            gameset.numExpectedParticipants = EGParameters['numExpectedParticipants'];
            gameset.numGames=EGParameters['numGames'];
            gameset.starttime=datetime.now();
            gameset.playmode=EGParameters['playMode'];
            gameset.job_id=EGParameters['job_id'];
            # 21
            db_session.add( gameset )
            db_session.commit()
            
            #creation of the part : link between user and gameset
            addIfNotFound = True # added in consent only
            part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)
            # 22
            part.gamesets.append(gameset);
            # keep data related to gameset in a dict
            gamesetsRunningList[str(gameset.id)]=dict()
            gamesetsRunningList[str(gameset.id)]['users']=dict()
            # 19082016 PG will force start after wait time will be elapsed
            # 12092016 PG
            # if EGParameters['forceStartAfterWait']=='y' :
            # 12092016 PG
            gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']=nowDate
            #print "gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']="+str(nowDate.strftime('%Y%m%d-%H%M%S-%f'))
            # 19082016
            if EGParameters['playMode']=='continuous':
              gamesetsRunningList[str(gameset.id)]['users_and_robots']=dict()
              continuousListOfChoices=[]
              for i in range(0,3):
                initlist=[]
                for j in range(0,EGParameters['numExpectedParticipants']):
                  initlist.append(0)
                continuousListOfChoices.append(initlist)
              gamesetsRunningList[str(gameset.id)]['continuousListOfChoices']=continuousListOfChoices
            # in addRobotsMode 
            if EGParameters['addRobotsMode']=='y' :
              # 'robots_process_state'='wait' : robots have not been started. Else 'robots_process_state'=='started' when robots will start.
              gamesetsRunningList[str(gameset.id)]['robots_process_state']='wait'
              gamesetsRunningList[str(gameset.id)]['robots']=dict()
              gamesetsRunningList[str(gameset.id)]['robotsnumber']=0
            gameset_pic_list=[]
            if EGParameters['useExistingGames']=='y':
              # choose random games among a list of games previously played (gameid are given in a text file opened in select_and_create_games function)
              # build a gameset picture with the images of these games gamesetsRunningList[str(gameset.id)]['games'][numgame]['game_pic_list']
              # keep games id as gameid_to_replay for each numgame gamesetsRunningList[str(gameset.id)][numgame]['gameid']= gameid
              # and workers decisions in each game/round gamesetsRunningList[str(gameset.id)][numgame]['game_workers_decisions'][workerid][numround][numdecision]=decisionvalue
              tab=select_and_create_games(EGParameters,gameset.id)
              gamesetsRunningList[str(gameset.id)]['tab_of_redundant_images']=tab['tab_of_redundant_images']
              gamesetsRunningList[str(gameset.id)]['games']=tab['games']
              for numgame in gamesetsRunningList[str(gameset.id)]['games']:
                gameset_pic_list.append(gamesetsRunningList[str(gameset.id)]['games'][numgame]['game_pic_list'])
            else :
              # all the images of the game set are put together in a same file called and sent to the client during the wait in room time
              # and the client extracts itself images of this file using javascript + canvas
              # This method has been choosed in order to not disturb the gamesets : a lot of gamesets can be played simultaneously and the number of requests can be important.
              # Using a big picture sent immediatly avoids to send a lot of smaller images during the gamesets : we hope that this method is more efficient than sending small images along the games
              # So, we have to create before the gameset starts :
              # - as many games as needed by the game set because of FK in table Image and Game = gameid
              # - a game set image containing the whole games images
              # first user sets a 'wait' status to current gameset
              for numgame in range(1,EGParameters['numGames']+1):
                game = Game(EGParameters);
                game.num = numgame;
                game.numExpectedParticipants = gameset.numExpectedParticipants;
                game.numRounds=EGParameters['numRounds'];
                game.gamesetid=gameset.id
                # 23
                db_session.add( game )
                db_session.commit()
                game_pic_list=[]
                for numimage in range(0,EGParameters['columnNumber']):
                  game_pic_list.append(game.image[numimage].pic_name)
                gameset_pic_list.append(game_pic_list)
            gameset.pic_name='gameset_'+str(gameset.id)+'_'+str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
            create_gameset_picture(EGParameters,gameset_pic_list,gameset.pic_name,int(EGParameters['imgsize']),int(EGParameters['imgsize']))
            #print "gameset.id=",gameset.id
            # 24
            game = db_session.query(Game).join(GameSet.games).filter(Game.num==1).filter(Game.gamesetid == gameset.id).one();
            gameset.games.append(game);
            part.games.append(game);
            
            hidId = str(gameset.id);
            assignmentId = str(gameset.id);            
            part.hitId = hidId;
            part.assignmentId = assignmentId;
            # 25
            db_session.commit()

        else:# gameset exists : user (or robot) added as a participant in the gameset
            # 26
            gamesetTuple = vacantGameSets.order_by(func.count('*').desc()).first()
            gameset = db_session.query(GameSet).get(gamesetTuple[0])
            
            #retrieval of the part : link between user and gameset
            addIfNotFound = True # added in consent only
            part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)            
            if(not part):
                raise ExperimentError('participant_not_found_gameset_exists_waiting_room')
            # 27
            part.gamesets.append(gameset)            
            game = db_session.query(Game).filter(Game.num==1).join(GameSet.games).filter(Game.gamesetid == gameset.id).one(); 
            # 28
            part.games.append(game)
            db_session.commit()
        # 23032015 : check for keyCodeMode
        if EGParameters['keyCodeMode']=='y':
          query_rs_keyCode="select count(*) as count from keycode_gameset_user"+\
                             " where userid="+str(user.id)+" and  status='IN_USE' and gamesetid=-1"
          rs_keyCode=engine.execute(query_rs_keyCode)
          row_rs_keyCode=rs_keyCode.fetchone()
          if(row_rs_keyCode['count']==1):
            query_rs_keyCode="update keycode_gameset_user set gamesetid="+str(gameset.id)+\
                            " where userid="+str(user.id)+" and  status='IN_USE' and gamesetid=-1"
            engine.execute(query_rs_keyCode)
          else:
            raise ExperimentError('user_has_0_or_more_than_1_keycode_in_use')
    elif (len(currentGamesets)== 1):# user in a non terminated gameset
        # 29
        gameset = currentGamesets[0];
        try:
          game = db_session.query(Game).join(GameSet).filter(Game.gamesetid==gameset.id).filter(Game.status==Game.STARTED).one()
        except:
          try:
            game = db_session.query(Game).join(GameSet).filter(Game.num==1).filter(Game.gamesetid==gameset.id).one()
          except:
            raise ExperimentError('game_not_found_for_gameset_not_terminated')
        #retrieval of the part : link between user and gameset
        addIfNotFound = False # added in consent only
        part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)
        if(not part):
            raise ExperimentError('participant_not_found_gameset_exists_waiting_room')
    else:
        print "Error, participant has started more than one game at the same time"
        raise ExperimentError('part_has_more_than_one_started_game')
                
    numParticipants = len(gameset.participants);
    # 30
    workerId = part.workerId
    assignmentId = part.assignmentId
    hitId = part.hitId
    sessionId = user.sessionId
    if request.args.has_key('robot'):
      if not workerId in gamesetsRunningList[str(gameset.id)]['robots']:#if robot not already in robots list
        gamesetsRunningList[str(gameset.id)]['robotsnumber']=gamesetsRunningList[str(gameset.id)]['robotsnumber']+1
        gamesetsRunningList[str(gameset.id)]['robots'][workerId]=dict()
        gamesetsRunningList[str(gameset.id)]['robots'][workerId]['robotnum']=gamesetsRunningList[str(gameset.id)]['robotsnumber']
    else:
      if not workerId in gamesetsRunningList[str(gameset.id)]['users']:
        gamesetsRunningList[str(gameset.id)]['users'][workerId]=dict()
        gamesetsRunningList[str(gameset.id)]['users'][workerId]['errorsize']=0
    if EGParameters['playMode']=='continuous' and not workerId in gamesetsRunningList[str(gameset.id)]['users_and_robots']:
      gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]=numParticipants-1
      #print 'workerId',workerId,'numpart',gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]
    
    # 19082016 
    # start the gameset if forceStartAfterWait is set and elapsed time in the waiting room for the first participant is greater than forceStartAfterWaitDelay
    # and forceStartAfterWaitNumParticipants = number of participants in the waiting room
    missingParticipant=gameset.numExpectedParticipants - numParticipants
    if EGParameters['forceStartAfterWait']=='y':
      missingParticipant=max(0,EGParameters['forceStartAfterWaitNumParticipants'] - numParticipants)
      #if (nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()>=EGParameters['forceStartAfterWaitDelay']*60 and EGParameters['forceStartAfterWaitNumParticipants']<=numParticipants:
      if missingParticipant==0:
        # if forceStartAfterWaitDelay has expired
        if (nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()>=EGParameters['forceStartAfterWaitDelay']*60:
          gameset.numExpectedParticipants=numParticipants
          #print "update games set numExpectedParticipants="+str(numParticipants)+" where gamesetid="+str(gameset.id)
          engine.execute("update games set numExpectedParticipants="+str(numParticipants)+" where gamesetid="+str(gameset.id))
          db_session.commit()
        # added 01112016
        else:
          leftDelayToBeginGameSet=EGParameters['forceStartAfterWaitDelay']*60-(nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()
    # 19082016
    stop_the_gameset_no_other_participant_timeleft=EGParameters['stop_the_gameset_no_other_participant_delay']*60-(nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()
    
    if(gameset.numExpectedParticipants > numParticipants):#not enough participants
      if (request.args.has_key('getFlag')):
        # start robots process if not already started. Robots process are started one time, not more when gamesetsRunningList[assignmentId]['robots_process_state']=='wait'
        # A robot cannot start robots process !
        #if not request.args.has_key('robot') and EGParameters['addRobotsMode']=='y' and EGParameters['useExistingGames']=='y' and gamesetsRunningList[assignmentId]['robots_process_state']=='wait':
        if not request.args.has_key('robot') and EGParameters['addRobotsMode']=='y' and gamesetsRunningList[assignmentId]['robots_process_state']=='wait':
          for i in range(0,gameset.numExpectedParticipants - numParticipants):
            os.spawnl(os.P_NOWAIT, r'C:\Program Files (x86)\PHP\php','php', str(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+'/robot_eg.php '))+str(EGParameters['httpPort']))
            #os.spawnl(os.P_NOWAIT, phpPath,'php', 'robot_eg.php ')
          gamesetsRunningList[assignmentId]['robots_process_state']='started'
        # end start robots process
        # 12092016 PG
        #print numParticipants, (nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()
        #print 'stop_the_gameset_no_other_participant_timeleft',stop_the_gameset_no_other_participant_timeleft
        if(EGParameters['stop_the_gameset_no_other_participant']=='y' and numParticipants==1 and (nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()>EGParameters['stop_the_gameset_no_other_participant_delay']*60):
          gamesetsRunningList[str(gameset.id)]['stop_the_gameset_no_other_participant_time']=nowDate
          gameset.status = GameSet.TERMINATED
          # 31
          db_session.commit()
          return json.dumps({'status':'stop_the_gameset_no_other_participant'})
        else:
        # 12092016 PG     
          return json.dumps({'activateTimer':EGParameters['activateTimer'],
                            'status':'Wait_in_room',
                            'missingParticipant':str(missingParticipant),
                            'timeLeft':str(int(leftDelayToBeginGameSet//60))+'mn '+str(int(leftDelayToBeginGameSet%60)),
                            'stop_the_gameset_no_other_participant':EGParameters['stop_the_gameset_no_other_participant'],
                            'stop_the_gameset_no_other_participant_timeleft':str(int(stop_the_gameset_no_other_participant_timeleft//60))+':'+str(int(stop_the_gameset_no_other_participant_timeleft%60)),
                            'numParticipants':numParticipants
                            }
                            )
      else:
        return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, sessionId=sessionId, workerId=workerId,
                                gameset_pic_name=gameset.pic_name,EGParameters=EGParameters)
    elif(gameset.numExpectedParticipants == numParticipants):#enough participants
      gameset.status = GameSet.STARTED
      game.status = Game.STARTED
      # 32
      db_session.commit()
      if (request.args.has_key('getFlag')):
          return json.dumps({'status':'GameSet_STARTED'})
      else:
          return start_exp_consensus(part)
    else:
      raise ExperimentError( 'too_many_participants' )

      
@app.route('/eg/intermediatepage', methods=['GET'])
def intermediate():# NOT USED ?
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=user.sessionId,EGParameters=EGParameters)
            

@app.route('/eg/expconsensus', methods=['GET','POST'])
def start_exp_consensus(part = None):
  if not EGParameters['EGRunning']:
    if (request.args.has_key('getFlag')):
      return json.dumps({'status':'EG_NOT_RUNNING'})
    else:
      return render_template('/eg/login.html',flag="LOGIN_NOT_OPEN",loginValues={'keyCodeBegin':'','username':'','loginsignin':'','pwd':'','pwd2':''}, EGParameters=EGParameters);

  # timeout for continuous mode : SOCIAL round stops on timeout, not on sent values from participants
  # continuous_list_of_decisions_of_a_participant : decisions taken by the current participant
  # In continuous mode, we should work just with 1 image, not 3 like in discrete mode
  # But it's easier to write code with 3 decisions like in discrete mode, so we currently work with 3 decisions corresponding to 3 images
  # In expconsensus.html, 3 decisions are sent : 2 are stored in hidden fields
  timeout=False
  #,isNewExpconsensusRound
  #print 'deb exp isNewExpconsensusRound',isNewExpconsensusRound
  #prevRoundChoicesSortedList=[]
  # check first to see if this hitId or assignmentId exists.  if so check to see if inExp is set
  if(part==None):#try to set part
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:#print "returning to login"
      return to_return
    #print 'starting experiment consensus',hitId, assignmentId, workerId
    # 33
    matches = Participant.query.\
                        filter(Participant.hitId == hitId).\
                        filter(Participant.assignmentId == assignmentId).\
                        filter(Participant.workerId == workerId).\
                        all()
    numrecs = len(matches)
    if numrecs == 0:
      print "Error, hit/assignment does not appear in database (serious problem)"
      raise ExperimentError( 'hit_assign_does_not_appear_in_database' )
    elif numrecs > 1:
      print "Error, hit/assignment appears in database more than once (serious problem)"
      raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )        
    else: # numrecs==1
      part = matches[0]            
  else : #"Participant given as parameter"
    hitId, assignmentId, workerId = part.hitId, part.assignmentId, part.workerId;
    user = User.query.filter(User.id==int(workerId)).one(); 
  
  if(len(part.gamesets)==0):#print "Going back to waiting room"
    return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId,gameset_pic_name="",EGParameters=EGParameters)
  gameset = part.gamesets[0];#gamesets[0] is the unique gameset of a participant
  try:
    curgame = db_session.query(Game).join(GameSet).filter(Game.gamesetid==gameset.id).filter(Game.status==Game.STARTED).one()
  except:
    try:
      curgame = db_session.query(Game).join(GameSet).filter(Game.num==1).filter(Game.gamesetid==gameset.id).one()
    except:
      raise ExperimentError('game_not_found_for_gameset_not_terminated')
  #curgame = db_session.query(Game).join(GameSet).filter(Game.gamesetid==gameset.id).filter(gameset.curGameNum()==Game.num).one()
  numParticipants = len(gameset.participants);
  if(gameset.numExpectedParticipants > numParticipants):
    # Preventing trouble
    return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, missingChoices=str(gameset.numExpectedParticipants - numParticipants),sessionId=user.sessionId,gameset_pic_name="",EGParameters=EGParameters)
  elif(gameset.numExpectedParticipants < numParticipants):
    raise ExperimentError( 'too_many_participants' )

  # Start the experiment = gameset.numExpectedParticipants == numParticipants
  imageurl = [];
  # 34
  if(Image.query.filter(Image.pic_type==EGParameters['imageType']).count()<3):
    raise ExperimentError('insuffisant_image_number')
  imageurl.append(EGParameters['estimationPicPath']+str(curgame.image[0].pic_name))
  imageurl.append(EGParameters['estimationPicPath']+str(curgame.image[1].pic_name))
  imageurl.append(EGParameters['estimationPicPath']+str(curgame.image[2].pic_name))
  
  if EGParameters['position_or_value']=='position' :
    if EGParameters['imageType']=='fractal' :
      question="Move the window over the picture and click where you think there is a maximum of color"
    else :
      question="Move the window over the picture and click where you think there is a maximum of items"
  else :
    if EGParameters['imageType']=='fractal' :
      question="What is the colour percentage in each image?"
    else :
      question="How many items do you see in each image?"

  color = [];
  # 35
  color.append(curgame.image[0].color)
  color.append(curgame.image[1].color)
  color.append(curgame.image[2].color)
  expconsensusAttributes = {'workerId': part.workerId,
                            'assignmentId': part.assignmentId,
                            'hitId' : part.hitId, 
                            'sessionId' : user.sessionId,
                            'cond' : part.cond, 
                            'counter' : part.counterbalance, 
                            'question' : question,                                                                            
                            'imageurl' : imageurl,
                            'color' : color,
                            'imageType' : EGParameters['imageType'],
                            'minDecisionValue' : EGParameters['minDecisionValue'],
                            'maxDecisionValue' : EGParameters['maxDecisionValue'],
                            'staticPath' : EGParameters['staticPath'],
                            'playMode' : EGParameters['playMode'],
                            'columnNumber' : EGParameters['columnNumber'],
                            'loneMaxReward' : EGParameters['loneMaxReward'],
                            'socialMaxReward' : EGParameters['socialMaxReward'],
                            'decision_out_of_limit_time' : EGParameters['decision_out_of_limit_time'],
                            'gameset_pic_name' : gameset.pic_name,
                            'displayerrorsize' : 'n',
                            'errorsize': 0
                            }
  # end debug
  #POST : form sent by user
  if(len(request.form)>0 and not request.form.has_key('No decision')):
    curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curgame.curRoundNum()==Round.num).one()
    # Add the participant new choice and decisions
    expconsensusAttributes['round']=curgame.curRoundNum();
    #print "not isChoiceMade(curround,part):",not isChoiceMade(curround,part),"curround.num == int(request.form['roundNum'])",curround.num, '==', int(request.form['roundNum'])
    # PG if(not isChoiceMade(curround,part) and curround.num == int(request.form['roundNum'])):
    if((not isChoiceMade(curround,part) or EGParameters['playMode']=='continuous') and curround.num == int(request.form['roundNum'])):
      #print request.form['decision0']
      decision0Value = request.form['decision0']
      decision1Value = request.form['decision1']
      decision2Value = request.form['decision2']
      auto0 = request.form['auto0']
      auto1 = request.form['auto1']
      auto2 = request.form['auto2']
      #print 'workerId',part.workerId,decision0Value, decision1Value,decision2Value
      # if auto==2, auto_reg=Decision.USER_MADE
      if int(auto0)==1:# in expconsensus : 0 is sent if user submit !!!
        auto_reg0 = Decision.AUTO;
      else:
        auto_reg0 = Decision.USER_MADE;
      if int(auto1)==1:
        auto_reg1 = Decision.AUTO;
      else:
        auto_reg1 = Decision.USER_MADE;
      if int(auto2)==1:
        auto_reg2 = Decision.AUTO;
      else:
        auto_reg2 = Decision.USER_MADE;
      registerChoice(part,curround,decision0Value,decision1Value,decision2Value,auto_reg0,auto_reg1,auto_reg2)
      # discrete : expconsensusAttributes['status'] = "CHOICE_MADE"
      if (curround.type==Round.LONE or EGParameters['playMode']=='discrete') :
        expconsensusAttributes['status'] = "CHOICE_MADE"
      else :
        expconsensusAttributes['status'] = "CHOICE_TO_BE_MADE"
      ## end if
      if (EGParameters['playMode']=='continuous') :
        if(EGParameters['imageType']=='fractal') :
          gamesetsRunningList[str(gameset.id)]['continuousListOfChoices'][0][gamesetsRunningList[str(gameset.id)]['users_and_robots'][part.workerId]]=float(decision0Value) 
        else :
          #print 'part.workerId : ',part.workerId
          gamesetsRunningList[str(gameset.id)]['continuousListOfChoices'][0][gamesetsRunningList[str(gameset.id)]['users_and_robots'][part.workerId]]=int(decision0Value)  

        ## end if
        # if testMode, generate a random choice for a simulated participant
        # if (EGParameters['testMode']=='y' and curround.type==Round.SOCIAL) :
          # randomSimulatedParticipant=random.randint(EGParameters['numExpectedParticipants'],EGParameters['numExpectedParticipants']+EGParameters['numSimulatedParticipants']-1)
          # continuousListOfChoices[0][randomSimulatedParticipant]=random.randint(int(EGParameters['minDecisionValue']),int(EGParameters['maxDecisionValue']))
        # ## end if
      ## end if
      # continuous version, suitable for discrete case :  distinct participants number in choices for this round
      # 36
      distinctParticipantsListChoiceInRound=db_session.query(distinct("'"+Choice.roundid+"::"+Choice.assignmentId+"::"+Choice.workerId)).filter(Choice.roundid==curround.id) 
      missingChoices = len(curgame.participants)-distinctParticipantsListChoiceInRound.count() 
      # before continuous version : missingChoices = len(curgame.participants)-len(curround.choices)
      expconsensusAttributes['missingChoices'] = str(missingChoices);
      # PG continuous if(missingChoices==0):
      if(missingChoices==0 and (curround.type==Round.LONE or EGParameters['playMode']=='discrete')):
        [htmlStatus,curround] = terminateRound(curround,curgame,gameset)
        if(htmlStatus!=""):
          expconsensusAttributes['status'] = htmlStatus
        ## end if
      ## end if
      # Redirect to an intermediate page to avoid double posting
      # PG continuous 
      # return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId)
      if (curround.type==Round.LONE or EGParameters['playMode']=='discrete') :
        return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId,EGParameters=EGParameters)
      ## end if
    # else: #Decision but no choice made
      # if(curround.num != int(request.form['roundNum'])):
          # #print "Problem : posting probably from old round to current round"
          # #print "This may be due to server lag. Aborting decision making. curround.num=",curround.num ,"request.form['roundNum']",request.form['roundNum']                                                                                                                                                                                  
      # ## end if
    ## end if
  ##end if form sent without field 'No decision'

  if(curgame.curRoundNum()==0):# Setting the first round
    curround = Round();
    curround.num = 1;
    curround.type = Round.LONE;
    if EGParameters['playMode']=='discrete':
      curround.maxreward = EGParameters['loneMaxReward'];
    else:
      curround.maxreward = 1
    curround.status = Round.STARTED
    curround.startTime = datetime.now()
    # 37
    curgame.rounds.append(curround)                                                                    
    db_session.commit()
  ## end if  
  # curgame and curround are ready
  # 38  
  curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curgame.curRoundNum()==Round.num).one()
  expconsensusAttributes['round']=curgame.curRoundNum();
  expconsensusAttributes['game']=len(part.games);
  if(curgame.curRoundNum()>1):# SOCIAL rounds
    # Past estimation to display : from previous round number or from same round number if continuous                                          
    if(EGParameters['playMode']=='discrete') :#discrete SOCIAL
      # 39
      prevround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(Round.num==curgame.curRoundNum()-1).one()
      prevchoice = db_session.query(Choice).filter(Choice.workerId == workerId and Choice.assignmentId == assignmentId).join(Round).join(Game).filter(Round.gameid==curgame.id).filter(Round.num==curgame.curRoundNum()-1).one()
      listprevround = prevround.listOfChoices()# decisions of all participants in the previous round [[decisions 0 of all part],[decisions 1 of all part],[decisions 2 of all part]]
      listprevchoice = prevchoice.listOfDecisions()# decisions of the workerId in the previous round
    else : #continuous SOCIAL : use the dynamic continuousListOfChoices
      listprevround=gamesetsRunningList[str(gameset.id)]['continuousListOfChoices']
      listprevchoice = [gamesetsRunningList[str(gameset.id)]['continuousListOfChoices'][0][gamesetsRunningList[assignmentId]['users_and_robots'][workerId]],0,0]
    ## end if
    listprevround = json.dumps(listprevround)
    expconsensusAttributes['prevRoundHTML']=listprevround;
    expconsensusAttributes['prevChoice']=listprevchoice;
      
  if(curround.type==Round.LONE):
    totalTime = EGParameters['loneRoundDuration'];
  elif(curround.type==Round.SOCIAL):
    totalTime = EGParameters['socialRoundDuration'];        
  remainingTime = timedelta(0,totalTime) + curround.startTime - datetime.now()
  expconsensusAttributes['remainingTime'] = remainingTime.seconds
  expconsensusAttributes['totalTime'] = totalTime
  
  # In order to don't disturb participants who are playing "seriously", we don't wait for answers of participants who didn't send a decision in the two
  # previous rounds.
  # To be considered as a "serious" participant again, a "non serious" participant has to send its answers before the last "serious" participant in the current round
  # If this participant is the "last serious one" for which we are waiting for, we will register choices of "non serious"
  # participants in the current round and go to the next one
  # Here we will know if all_serious_workers_have_chosen : if true the round will be terminated as if remaining time was out of limit below
  # select participants who answered automatically in the 2 previous rounds :
  # curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curgame.curRoundNum()==Round.num).one()
  
  check_for_all_serious_workers_have_chosen='n'
  all_serious_workers_have_chosen=False
  if(check_for_all_serious_workers_have_chosen=='y'):# check or not ?
    all_serious_workers_have_chosen=serious_workers_have_chosen(gameset,curgame,curround,EGParameters)

  # an explicit POST or a jquery triggered GET, if remaining time is out of limit : 
  # Register choices automatically for participants without choice made in the current game of the curround
  # or "serious" participants have already sent their decision in this round
  
  if(remainingTime<=timedelta(days=0,seconds=-EGParameters['decision_out_of_limit_time']) or remainingTime>timedelta(days=0,seconds=1000)):# or (check_for_all_serious_workers_have_chosen=='y' and all_serious_workers_have_chosen)
    timeout=True# PG : add timeout for continuous 
    boolIntermediatePage = False
    #print 'if remaining time out of limit'
    if(not isChoiceMade(curround,part)):
      boolIntermediatePage = True
    defaultDecisionValue=0 #no decision value
    for each_part in curgame.participants:
      if(not isChoiceMade(curround,each_part)):
        registerChoice(each_part,curround,defaultDecisionValue,defaultDecisionValue,defaultDecisionValue,Decision.AUTO,Decision.AUTO,Decision.AUTO)
    expconsensusAttributes['status'] = "CHOICE_MADE" # default : may be changed if(missingChoices==0) bellow 
    if(EGParameters['playMode']=='discrete') : #20/03/2014
      # 40
      missingChoices = len(curgame.participants)-len(curround.choices)
    else:
      # continuous version : distinct participants number in choices for this round
      # 41
      distinctParticipantsListChoiceInRound=db_session.query(distinct("'"+Choice.roundid+"::"+Choice.assignmentId+"::"+Choice.workerId)).filter(Choice.roundid==curround.id) 
      missingChoices = len(curgame.participants)-distinctParticipantsListChoiceInRound.count()
    ## end if
    expconsensusAttributes['missingChoices'] = str(missingChoices);
    if(missingChoices==0):
      #print 'if remaining time out of limit, if missingChoices==0'
      [htmlStatus,curround] = terminateRound(curround,curgame,gameset)
      if(htmlStatus!=""):
        expconsensusAttributes['status'] = htmlStatus
    # Redirect to an intermediate page to avoid double posting
    if(boolIntermediatePage):
      return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId,EGParameters=EGParameters)
      
  #curgame = db_session.query(Game).join(GameSet).filter(Game.gamesetid==gameset.id).filter(gameset.curGameNum()==Game.num).one()
  try:
    # 42
    curgame = db_session.query(Game).join(GameSet).filter(Game.gamesetid==gameset.id).filter(Game.status==Game.STARTED).one()
  except:
    try:
      curgame = db_session.query(Game).join(GameSet).filter(Game.num==1).filter(Game.gamesetid==gameset.id).one()
    except:
      raise ExperimentError('game_not_found_for_gameset_not_terminated')
  # 43
  curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curgame.curRoundNum()==Round.num).one()    
  
  if(isChoiceMade(curround,part)):# isChoiceMade==true if this participant choices have been registered in DB for the current round/game/gameset
    # PG : expconsensusAttributes['status'] = "CHOICE_MADE"
    if(curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout):
      expconsensusAttributes['status'] = "CHOICE_MADE"
      # 20140320 
      """if(timeout):
        expconsensusAttributes['round'] = curround.num+1"""
    else: # continuous social round
      expconsensusAttributes['status'] = "CHOICE_TO_BE_MADE"
    # continuous version : distinct participants number in choices for this round
    # 44
    distinctParticipantsListChoiceInRound=db_session.query(distinct("'"+Choice.roundid+"::"+Choice.assignmentId+"::"+Choice.workerId)).filter(Choice.roundid==curround.id) 
    missingChoices = len(curgame.participants)-distinctParticipantsListChoiceInRound.count() 
    # before continuous version : missingChoices = len(curgame.participants)-len(curround.choices)
    expconsensusAttributes['missingChoices'] = str(missingChoices)
    # before continuous version : if(missingChoices==0 and curround.num == curgame.numRounds):
    if(missingChoices==0 and curround.num == curgame.numRounds and (curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout)):
      if(curgame.num==gameset.numGames):
        expconsensusAttributes['status'] = "GAMESET_OVER"
        gameset.status = GameSet.TERMINATED;
        # 45
        db_session.commit()
      else:
        #if(curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout):
        #print "if(curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout)"
        expconsensusAttributes['status'] = "GAME_OVER"
        curgame.status = Game.TERMINATED;
        # 46
        newgame = db_session.query(Game).filter(Game.num == curgame.num+1).filter(Game.gamesetid == gameset.id).one();
        newgame.status=Game.STARTED
        #newgame.num = curgame.num+1;
        #newgame.numRounds=EGParameters['numRounds'];
        #newgame.numExpectedParticipants = gameset.numExpectedParticipants;
        gameset.games.append(newgame);
        for each_part in gameset.participants:
          each_part.games.append(newgame);
        # 47
        db_session.commit()
        """isNewExpconsensusRound=[]          
        for i in range(0,EGParameters['numExpectedParticipants']):
          isNewExpconsensusRound.append("True")"""
  else:
    expconsensusAttributes['status'] = "CHOICE_TO_BE_MADE"
  ##end if
  
  if(curround.type==Round.LONE):
    expconsensusAttributes['roundType'] = "LONE";                
  else:
    expconsensusAttributes['roundType'] = "SOCIAL";
  ##end if
  expconsensusAttributes['reward'] = curround.maxreward;
  # display average of errorsize in the 3 previous games during the first round
  if part.workerId in gamesetsRunningList[str(gameset.id)]['users']:
    if curgame.num%3==1 and curgame.num!=1 and curround.num ==1:
      expconsensusAttributes['displayerrorsize']='y'
    else:
      expconsensusAttributes['displayerrorsize']='n'
    expconsensusAttributes['errorsize'] = gamesetsRunningList[str(gameset.id)]['users'][workerId]['errorsize']
  if (request.args.has_key('getFlag')): # answer to the periodical GET sent by user client in expconsensus.html with js timer setInterval 
    if(request.args.has_key('robot')) and EGParameters['addRobotsMode']=='y' and EGParameters['useExistingGames']=='y':
      robotnum=gamesetsRunningList[str(gameset.id)]['robots'][workerId]['robotnum']
      expconsensusAttributes['robotnum']=robotnum
      expconsensusAttributes['givenanswers']='yes'
      expconsensusAttributes['decisiontime']=random.randint(0,EGParameters[expconsensusAttributes['roundType'].lower()+'RoundDuration']//2)
      #expconsensusAttributes['decisiontime']=gamesetsRunningList[str(gameset.id)]['games'][curgame.num]['game_workers_decisions'][robotnum][curround.num]['decisiontime']
      expconsensusAttributes['decisions']=''
      first=True
      for decisionnum in range(0,3):
        sep='#'
        if first :
          sep=''
          first=False        
        expconsensusAttributes['decisions']=expconsensusAttributes['decisions']+sep+str(gamesetsRunningList[str(gameset.id)]['games'][curgame.num]['game_workers_decisions'][robotnum][curround.num]['decisions'][decisionnum])
    return json.dumps(expconsensusAttributes)
    
  else: # post made in expconsensus
    if curround.type==Round.LONE or EGParameters['playMode']=='discrete':
      expconsensusAttributes['sessionId']=user.sessionId
      return render_expconsensus(part,**expconsensusAttributes)
    else :
      return ('', 204)
      # expconsensusAttributes['success'] = True
      # expconsensusAttributes['message'] = 'Success!';
      # return json.dumps(expconsensusAttributes)#
  ##end if

def render_expconsensus(part,**expconsensusAttributes):
    if(part.status < Participant.STARTED):
        part.status=Participant.STARTED
        if expconsensusAttributes['status'] == "CHOICE_TO_BE_MADE":
          expconsensusAttributes['sound']=1
        else :
          expconsensusAttributes['sound']=0
    else:
        expconsensusAttributes['sound']=0
    return render_template('/eg/expconsensus.html',EGParameters=EGParameters, **expconsensusAttributes)
        
def terminateRound(curround,curgame,gameset) :
  # 16/03 init decisions to 0 if end of game
  global gamesetsRunningList
  global EGParameters#,isNewExpconsensusRound
  """isNewExpconsensusRound=[]          
  for i in range(0,EGParameters['numExpectedParticipants']):
    isNewExpconsensusRound.append("True")"""
  # 20150502 : redundant images in discrete mode : adjust decisions of robots with the user decisons in the previous game with original image
  #print 'curround.status',curround.status
  if EGParameters['redundantMode']=='y' and curround.status!=Round.TERMINATED:
    for decisionnum in range(0,EGParameters['columnNumber']):
      if str(curgame.num)+'#'+str(curround.num)+'#'+str(decisionnum) in gamesetsRunningList[str(gameset.id)]['tab_of_redundant_images']:
        #print str(curgame.num)+'#'+str(curround.num)+'#'+str(decisionnum),' redundant of ',gamesetsRunningList[str(gameset.id)]['tab_of_redundant_images'][str(curgame.num)+'#'+str(curround.num)+'#'+str(decisionnum)]
        # robotsdecisions='robot'
        # for robotworkerId in gamesetsRunningList[str(gameset.id)]['robots']:
          # robotnum=gamesetsRunningList[str(gameset.id)]['robots'][robotworkerId]['robotnum']
          # #for robotnum in gamesetsRunningList[str(gameset.id)]['games'][curgame.num]['game_workers_decisions']:
          # robotsdecisions=robotsdecisions+' num:'+str(robotnum)+' id:'+str(robotworkerId)+' dec:'+str(gamesetsRunningList[str(gameset.id)]['games'][curgame.num]['game_workers_decisions'][robotnum][curround.num]['decisions'][decisionnum])+'#'
        # print robotsdecisions
        # user's decision in curgame, round 1, decisionnum (0,1 and 2) for this redundant image
        # 48
        userworkerId=gamesetsRunningList[str(gameset.id)]['users'].keys()[0];
        query_rs= "select decisions.value,decisions.status from decisions,choices,rounds,games"+\
                  " where decisions.choiceid=choices.id and choices.roundid=rounds.id and rounds.gameid=games.id and choices.workerId="+str(userworkerId)+\
                  " and games.num="+str(curgame.num)+" and rounds.num=1 and decisions.num="+str(decisionnum)+" and games.gamesetid="+str(gameset.id)
        rs=engine.execute(query_rs)
        row_rs=rs.fetchone()
        if row_rs['status']==Decision.USER_MADE :
          currentdecisionval=row_rs['value']
          # user's decision in game, round 1, decision num for the previous occurence of this redundant image
          tab=split(gamesetsRunningList[str(gameset.id)]['tab_of_redundant_images'][str(curgame.num)+'#'+str(curround.num)+'#'+str(decisionnum)],'#')
          query_rs= "select decisions.value,decisions.status from decisions,choices,rounds,games"+\
                    " where decisions.choiceid=choices.id and choices.roundid=rounds.id and rounds.gameid=games.id and choices.workerId="+str(userworkerId)+\
                    " and games.num="+str(tab[0])+" and rounds.num=1 and decisions.num="+str(tab[2])+" and games.gamesetid="+str(gameset.id)
          rs=engine.execute(query_rs)
          row_rs=rs.fetchone()
          if row_rs['status']==Decision.USER_MADE :
            delta=currentdecisionval-row_rs['value']
            #print 'delta:',delta
            engine.execute("update decisions,choices,rounds,games set decisions.value=least("+EGParameters['maxDecisionValue']+",greatest("+EGParameters['minDecisionValue']+",decisions.value+"+str(delta)+"))"\
                            " where decisions.choiceid=choices.id and choices.roundid=rounds.id and rounds.gameid=games.id and choices.workerId<>"+str(userworkerId)+\
                            " and games.num="+str(curgame.num)+" and rounds.num="+str(curround.num)+" and decisions.num="+str(decisionnum)+" and games.gamesetid="+str(gameset.id))
            db_session.commit()
  curround.status=Round.TERMINATED;
  curround.endTime = datetime.now()
  htmlStatus = "";
  if(curround.num==curgame.numRounds):
    if(curgame.num==gameset.numGames):
      htmlStatus = "GAMESET_OVER"
      gameset.status = GameSet.TERMINATED;
      #curgame.status = Game.TERMINATED;
    else:
      htmlStatus = "GAME_OVER"
      curgame.status = Game.TERMINATED;
      # 49
      newgame = db_session.query(Game).filter(Game.num == curgame.num+1).filter(Game.gamesetid == gameset.id).one();
      #nextgame.num = curgame.num+1;
      #nextgame.numRounds=EGParameters['numRounds'];
      #nextgame.numExpectedParticipants = gameset.numExpectedParticipants;
      newgame.status=Game.STARTED
      # 50
      gameset.games.append(newgame);
      for each_part in gameset.participants:
        each_part.games.append(newgame);
      curround = startNewRound(newgame)
      # 51
      db_session.commit()
    
      # 16/03 init
      if EGParameters['playMode']=='continuous':
        continuousListOfChoices=[]
        for i in range(0,3):
          initlist=[]
          # 19082016
          #for j in range(0,EGParameters['numExpectedParticipants']):
          for j in range(0,gameset.numExpectedParticipants):
          # 19082016
            initlist.append(0)
          continuousListOfChoices.append(initlist)
        gamesetsRunningList[str(gameset.id)]['continuousListOfChoices']=continuousListOfChoices
  else:
    # Starting a new round
    curround = startNewRound(curgame)
  
  return [htmlStatus,curround]

def startNewRound(curgame):
# Starting a new round in the game curgame (requires curgame not to be over)
    curround = Round()
    curround.num = curgame.curRoundNum()+1
    if((curgame.num==1 and curround.num<=1) or (curgame.num>1 and curround.num==1)):
        curround.type = Round.LONE;
        if EGParameters['playMode']=='discrete':
          curround.maxreward = EGParameters['loneMaxReward'];
        else:
          curround.maxreward = 1
    else:
        curround.type = Round.SOCIAL;
        if EGParameters['playMode']=='discrete':
          curround.maxreward = EGParameters['socialMaxReward'];
        else:
          curround.maxreward = 1        
    curround.status = Round.STARTED
    curround.startTime = datetime.now()
    # 52
    curgame.rounds.append(curround)
    db_session.commit()
    return curround
    
def registerChoice(part,curround,decision0Value,decision1Value,decision2Value,auto0,auto1,auto2):
    decision0 = Decision()
    decision1 = Decision()
    decision2 = Decision()
    decision0.num = 0
    decision1.num = 1
    decision2.num = 2
    decision0.value = decision0Value 
    decision1.value = decision1Value
    decision2.value = decision2Value
    decision0.status = auto0
    decision1.status = auto1
    decision2.status = auto2
    # currently percent contains a percent for fractal or a number for peanut
    errorsize0 = abs(float(decision0.value) - curround.game.image[0].percent)/EGParameters['ratioForErrorSize'];
    errorsize1 = abs(float(decision1.value) - curround.game.image[1].percent)/EGParameters['ratioForErrorSize'];
    errorsize2 = abs(float(decision2.value) - curround.game.image[2].percent)/EGParameters['ratioForErrorSize'];                                                            
    decision0.reward = reward(errorsize0,curround.maxreward);                            
    decision1.reward = reward(errorsize1,curround.maxreward);
    decision2.reward = reward(errorsize2,curround.maxreward);
    # 15/04/2014
    decision0.imageid = curround.game.image[0].id;
    decision1.imageid = curround.game.image[1].id;
    decision2.imageid = curround.game.image[2].id;                                                            

    timestamp=datetime.now()
    decision0.timestamp=timestamp
    decision1.timestamp=timestamp
    decision2.timestamp=timestamp
                         
    choice = Choice()
    choice.decisions.append(decision0)
    choice.decisions.append(decision1)
    choice.decisions.append(decision2)
    choice.workerId = part.workerId;
    choice.assignmentId = part.assignmentId;
    choice.roundid = curround.id;
    # 53
    curround.choices.append(choice)
    part.choices.append(choice)
    db_session.commit()
    # store user errorsizes. After 3 games, the average is computed with 3 rounds/game
    if part.workerId in gamesetsRunningList[part.assignmentId]['users']:# not a robot
      if curround.num==1 and curround.game.num%3==1 :
        gamesetsRunningList[part.assignmentId]['users'][part.workerId]['errorsize']=int(errorsize0+errorsize1+errorsize2)
      elif curround.num==3 and curround.game.num%3==0 :
        gamesetsRunningList[part.assignmentId]['users'][part.workerId]['errorsize']=int(gamesetsRunningList[part.assignmentId]['users'][part.workerId]['errorsize']/27)*EGParameters['ratioForErrorSize'];
      else :
        gamesetsRunningList[part.assignmentId]['users'][part.workerId]['errorsize']=int(errorsize0+errorsize1+errorsize2+gamesetsRunningList[part.assignmentId]['users'][part.workerId]['errorsize'])
    while(not isChoiceMade(curround,part)):
      pass
        
def reward(errorsize,maxreward):
  if EGParameters['playMode']=='discrete':
    if(errorsize<2):
        weight = 1;
    elif(errorsize<5):
        weight = 0.5;
    elif(errorsize<15):
        weight = 0.2;
  else: #continuous
    if(errorsize<5):
        weight = 1;
    else:
        weight = 0;

    return weight*maxreward;
    #return maxreward;
        
def isChoiceMade(curround,part):
    matching_choices = db_session.query(Round).join(Choice).filter(Round.id == curround.id).filter(Choice.workerId==part.workerId and Choice.assignmentId==part.assignmentId).all()
    return len(matching_choices)>0

@app.route('/eg/inexp', methods=['POST'])
def enterexp():
    """
    AJAX listener that listens for a signal from the user's script when they
    leave the instructions and enter the real experiment. After the server
    receives this signal, it will no longer allow them to re-access the
    experiment applet (meaning they can't do part of the experiment and
    referesh to start over).
    """
    if not request.form.has_key('assignmentId'):
        print "No assignmentId in inexp route enterexp"
        raise ExperimentError('improper_inputs')
    assignmentId = request.form['assignmentId']
    user = Participant.query.\
            filter(Participant.assignmentId == assignmentId).\
            one()
    user.status = Participant.STARTED
    user.beginexp = datetime.now()
    db_session.add(user)
    db_session.commit()
    
    # Link the participant to a Game
    game = link_participant_to_game(user);
    return "Success"

@app.route('/eg/inexpsave', methods=['POST'])
def inexpsave():
    """
    The experiments script updates the server periodically on subjects'
    progress. This lets us better understand attrition.
    """
    print "accessing the /inexpsave route"
    #print request.form.keys()
    if request.form.has_key('assignmentId') and request.form.has_key('dataString'):
        assignmentId = request.form['assignmentId']
        datastring = request.form['dataString']  
        #print "getting the save data", assignmentId, datastring
        user = Participant.query.\
                filter(Participant.assignmentId == assignmentId).\
                one()
        user.datastring = datastring
        user.status = User.STARTED
        db_session.add(user)
        db_session.commit()
    return render_template('/eg/error.html', errornum= experiment_errors['intermediate_save'],EGParameters=EGParameters)

@app.route('/eg/quitter', methods=['POST'])
def quitter():
    """
    Subjects post data as they quit, to help us better understand the quitters.
    """
    print "accessing the /quitter route"
    print request.form.keys()
    if request.form.has_key('assignmentId') and request.form.has_key('dataString'):
        assignmentId = request.form['assignmentId']
        datastring = request.form['dataString']  
        print "getting the save data", assignmentId, datastring
        user = Participant.query.\
                filter(Participant.assignmentId == assignmentId).\
                one()
        user.datastring = datastring
        user.status = Participant.QUITEARLY
        db_session.add(user)
        db_session.commit()
    return render_template('/eg/error.html', errornum= experiment_errors['tried_to_quit'])

@app.route('/eg/questionnaire_first', methods=['POST', 'GET'])
def questionnaire_first():
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    if request.method == 'GET':
      try:
          questionnaires = Questionnaire.query.filter(Questionnaire.userid == int(workerId)).all()
          baseQuestionnaire = questionnaires[0]
      except:
          baseQuestionnaire = None
      try:
          questionnaire = Questionnaire.query.filter(Questionnaire.userid == int(workerId)).filter(Questionnaire.gamesetid== int(hitId)).one()
      except:
          questionnaire = Questionnaire();
          questionnaire.userid = int(workerId)
          questionnaire.gamesetid = int(hitId)
          db_session.add(questionnaire);
      if(baseQuestionnaire!=None):
          questionnaire.enterQtime=datetime.now()
          questionnaire.anxious = baseQuestionnaire.anxious
          questionnaire.calm = baseQuestionnaire.calm
          questionnaire.conventional = baseQuestionnaire.conventional
          questionnaire.critical = baseQuestionnaire.critical
          questionnaire.dependable = baseQuestionnaire.dependable
          questionnaire.disorganized = baseQuestionnaire.disorganized
          questionnaire.extraverted = baseQuestionnaire.extraverted
          questionnaire.open = baseQuestionnaire.open
          questionnaire.reserved = baseQuestionnaire.reserved
          questionnaire.sympathetic = baseQuestionnaire.sympathetic  
          questionnaire.sexe =  baseQuestionnaire.sexe
          questionnaire.nativespeakenglish =  baseQuestionnaire.nativespeakenglish
          questionnaire.schoolgrade =  baseQuestionnaire.schoolgrade
      db_session.commit();      
      questionnaireHTML = { "workerId": workerId,
        "hitId": hitId,
        "assignmentId": assignmentId,
        "sessionId":user.sessionId,        
        "anxious" : questionnaire.anxious,
        "calm":questionnaire.calm,
        "conventional":questionnaire.conventional,
        "critical":questionnaire.critical,
        "dependable":questionnaire.dependable,
        "disorganized":questionnaire.disorganized,
        "extraverted":questionnaire.extraverted,
        "open":questionnaire.open,
        "reserved":questionnaire.reserved,
        "sympathetic":questionnaire.sympathetic,
        "sexe":questionnaire.sexe,
        "nativespeakenglish":questionnaire.nativespeakenglish,
        "schoolgrade":questionnaire.schoolgrade
      }
      if(request.args.has_key('getFlag')):            
          return render_template('/eg/questionnaire_first.html', **questionnaireHTML)
      else:
          return render_template('/eg/questionnaire_first.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId,EGParameters=EGParameters)
    else : #request.method == 'POST'
        # added for robot
        if request.args.has_key('robot'):
          questionnaire = Questionnaire();
          questionnaire.userid = int(workerId)
          questionnaire.gamesetid = int(hitId)
          db_session.add(questionnaire);
          db_session.commit()
        # end added for robot
        
        questionnaire = Questionnaire.query.filter(Questionnaire.userid == int(workerId)).filter(Questionnaire.gamesetid== int(hitId)).one()

        questionnaire.leaveQtime=datetime.now()
        questionnaire.anxious = request.form['anxious']
        questionnaire.calm = request.form['calm']
        questionnaire.conventional = request.form['conventional']
        questionnaire.critical = request.form['critical']
        questionnaire.dependable = request.form['dependable']
        questionnaire.disorganized = request.form['disorganized']
        questionnaire.extraverted = request.form['extraverted']
        questionnaire.open = request.form['open']
        questionnaire.reserved = request.form['reserved']
        questionnaire.sympathetic = request.form['sympathetic']
        questionnaire.sexe = request.form['sexe']
        questionnaire.nativespeakenglish = request.form['nativespeakenglish']
        questionnaire.schoolgrade = request.form['schoolgrade']
        user.status = User.ASSESSED
        db_session.commit()        
        return render_template('/eg/instruct.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId,EGParameters=EGParameters)
    
@app.route('/eg/debriefing', methods=['POST', 'GET'])
def debriefing():
    """
    User has finished the experiment and is posting their data in the form of a
    (long) string. They will receive a debriefing back.
    """
    htmltable=''# ajout 08/03/2016
    totalreward = 0;
    bonus="0";
    maxpoints=0.0
    keyCodeEnd='';
    
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    
    
    try:
        part = Participant.query.\
                filter(Participant.assignmentId == assignmentId).\
                filter(Participant.workerId == workerId).\
                one()
    except:
        raise ExperimentError('improper_inputs')
    
    # init tab_userdecision

    if(workerId in gamesetsRunningList[part.assignmentId]['users']): # not a robot
      gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision']=dict()
    
      if EGParameters['playMode']=='discrete':
        maxpoints=EGParameters['numGames']*(EGParameters['loneMaxReward']+(EGParameters['numRounds']-1)*EGParameters['socialMaxReward'])
        for choice in part.choices:
          round=choice.round
          game=round.game
          gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][game.num]=dict()
          for decision in choice.decisions:
            decisionval=decision.value
            if(EGParameters['imageType'] == 'peanut'):
              decisionval=int(decision.value)
            gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][game.num][decision.num+1]=decisionval
            if(decision.status==Decision.USER_MADE):
              totalreward = random.randint(int(maxpoints/2),maxpoints) # A REFAIRE totalreward + decision.reward;
        #if totalreward>EGParameters['bonusFloor']*maxpoints :
          #bonus=1
      # begin calculation continuous 08/03/2016
      else : #EGParameters['playMode']=='continuous'
        query_rs="select count(*) as numrows"+\
                   " from decisions, choices, rounds, games where decisions.choiceid=choices.id and choices.roundid=rounds.id"+\
                   " and rounds.gameid=games.id"+\
                   " and choices.assignmentid='"+part.assignmentId+"' and choices.workerid='"+part.workerId+"'"+\
                   " and decisions.num=0"+\
                   " order by decisions.timestamp asc"
        rs=engine.execute(query_rs)
        row_rs=rs.fetchone()
        numrows=row_rs['numrows']
        query_rs="select games.num as gamenum,games.id as gameid,"+\
                   "rounds.num as roundnum,rounds.type as roundtype,rounds.startTime as roundstarttime,rounds.endTime as roundendtime,"+\
                   " decisions.timestamp as decisiontime, decisions.status, decisions.value as decisionval, decisions.reward"+\
                   " from decisions, choices, rounds, games"+\
                   " where decisions.choiceid=choices.id and choices.roundid=rounds.id"+\
                   " and rounds.gameid=games.id"+\
                   " and choices.assignmentid='"+part.assignmentId+"' and choices.workerid='"+part.workerId+"'"+\
                   " and decisions.num=0"+\
                   " order by decisions.timestamp asc"
        rs=engine.execute(query_rs)
        prev_roundnum=-1
        prev_roundstarttime=""
        prev_decisiontime=""
        prev_reward=0
        prev_roundtype=Round.LONE
        duration=0
        indexrow=0
        htmltable=htmltable+'<table border="1"><tr><td nowrap>game</td><td nowrap>round</td><td nowrap>type</td><td nowrap>roundstart</td><td nowrap>roundend</td><td nowrap>prev decision</td><td nowrap>decision</td><td nowrap>duration</td><td nowrap>prev_decisionval</td><td nowrap>prev_reward</td><td nowrap>prev_reward*duration</td><td nowrap align="center">formule</td><td nowrap align="center">condition</td></tr>'
        for row_rs in rs :
          htmltable=htmltable+'<tr>'
          indexrow=indexrow+1
          gamenum=row_rs['gamenum']
          roundnum=row_rs['roundnum']
          roundtype=row_rs['roundtype']
          roundstarttime=row_rs['roundstarttime']
          roundendtime=row_rs['roundendtime']
          decisiontime=row_rs['decisiontime']
          decisionval=row_rs['decisionval']
          if(EGParameters['imageType'] == 'peanut'):
            decisionval=int(row_rs['decisionval'])
          reward=row_rs['reward']
          formule=''
          if roundtype==Round.LONE :# compute previous duration between decision and end of round 
            if gamenum==1 :
              htmltable=htmltable+'<td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>LONE</td><td nowrap>'+roundstarttime.strftime("%H:%M:%S")+\
                                  '</td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap>'+\
                                  '</td><td nowrap>'+decisiontime[11:]+'</td><td nowrap></td><td nowrap></td><td nowrap>'+\
                                  '</td><td nowrap></td><td nowrap></td><td nowrap>LONE et gamenum=1</td>'
            else :
              duration=max(0,(prev_roundstarttime-(datetime.strptime(prev_decisiontime, "%Y-%m-%d %H:%M:%S"))).total_seconds()+EGParameters['socialRoundDuration']+EGParameters['decision_out_of_limit_time'])
              formule='(prev_roundstarttime+socialRoundDuration+decision_out_of_limit_time)-prev_decisiontime'
              htmltable=htmltable+'<td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>LONE</td><td nowrap>'+roundstarttime.strftime("%H:%M:%S")+\
                                  '</td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap class="red16"><b>'+prev_decisiontime[11:]+\
                                  '</b></td><td nowrap>'+decisiontime[11:]+'</td><td nowrap>'+str(duration)+'</td><td nowrap>'+str(prev_decisionval)+'</td><td nowrap>'+\
                                  str(prev_reward)+'</td><td nowrap>'+str(prev_reward*duration)+'</td><td nowrap>'+formule+'</td><td nowrap>LONE et gamenum!=1</td>'
              # last decision in the SOCIAL round of the previous game
              gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][gamenum-1]=dict()
              gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][gamenum-1][1]=prev_decisionval
          else :
            if prev_roundnum!=roundnum :
              # duration from the begining of the SOCIAL round and the first decision in the SOCIAL round
              duration=max(0,(datetime.strptime(decisiontime, "%Y-%m-%d %H:%M:%S")-roundstarttime).total_seconds())
              formule='decisiontime-roundstarttime'
              htmltable=htmltable+'<td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>SOCIAL</td><td nowrap class="red16"><b>'+roundstarttime.strftime("%H:%M:%S")+'</b></td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap>'+prev_decisiontime[11:]+'</td><td nowrap class="red16"><b>'+decisiontime[11:]+'</b></td><td nowrap>'+str(duration)+'</td><td nowrap>'+str(prev_decisionval)+'</td><td nowrap>'+str(prev_reward)+'</td><td nowrap>'+str(prev_reward*duration)+'</td><td nowrap>'+formule+'</td><td nowrap>1ere decision et SOCIAL</td>'
            else:
              # duration between two decisions in the SOCIAL round          
              duration=max(0,(datetime.strptime(decisiontime, "%Y-%m-%d %H:%M:%S")-datetime.strptime(prev_decisiontime, "%Y-%m-%d %H:%M:%S")).total_seconds())            
              formule='decisiontime-previous_decisiontime '
              htmltable=htmltable+'<td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>SOCIAL</td><td nowrap>'+roundstarttime.strftime("%H:%M:%S")+'</td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap class="red16"><b>'+prev_decisiontime[11:]+'</b></td><td nowrap class="red16"><b>'+decisiontime[11:]+'</b></td><td nowrap>'+str(duration)+'</td><td nowrap>'+str(prev_decisionval)+'</td><td nowrap>'+str(prev_reward)+'</td><td nowrap>'+str(prev_reward*duration)+'</td><td nowrap>'+formule+'</td><td nowrap>decision SOCIAL</td>'
          totalreward=totalreward+prev_reward*duration
          prev_roundstarttime=roundstarttime
          prev_decisiontime=decisiontime
          prev_reward=reward
          prev_roundnum=roundnum
          prev_decisionval=decisionval
          htmltable=htmltable+'</tr>'
        # end of result set : last decision in the last social round 
        duration=max(0,(roundstarttime-(datetime.strptime(decisiontime, "%Y-%m-%d %H:%M:%S"))).total_seconds()+EGParameters['socialRoundDuration']+EGParameters['decision_out_of_limit_time'])
        formule='(roundstarttime+socialRoundDuration+decision_out_of_limit_time)-timedecision'
        totalreward=totalreward+reward*duration
        htmltable=htmltable+'<tr><td nowrap>game</td><td nowrap>round</td><td nowrap>type</td><td nowrap>roundstart</td><td nowrap>roundend</td><td nowrap>prev decision</td><td nowrap>decision</td><td nowrap>duration</td><td nowrap>decisionval</td><td nowrap>reward</td><td nowrap>reward*duration</td><td nowrap align="center">formule</td><td nowrap align="center">condition</td></tr>'
        htmltable=htmltable+'<tr><td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>SOCIAL</td><td nowrap class="red16"><b>'+roundstarttime.strftime("%H:%M:%S")+'</b></td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap>'+prev_decisiontime[11:]+'</td><td nowrap class="red16"><b>'+decisiontime[11:]+'</b></td><td nowrap>'+str(duration)+'</td><td nowrap>'+str(decisionval)+'</td><td nowrap>'+str(reward)+'</td><td nowrap>'+str(reward*duration)+'</td><td nowrap>'+formule+'</td><td nowrap>derniere decision et SOCIAL</td></tr>'
        htmltable=htmltable+'</table>'
        
        # last decision in the last social round
        gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][gamenum]=dict()
        gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][gamenum][1]=prev_decisionval

        #maxpoints=EGParameters['numGames']*(1+(EGParameters['socialRoundDuration']+4)) # 1 in LONE, socialRoundDuration+4 in SOCIAL
        maxpoints=EGParameters['numGames']*(EGParameters['socialRoundDuration']+EGParameters['decision_out_of_limit_time']) # 1 in LONE, socialRoundDuration+4 in SOCIAL
        #if totalreward>EGParameters['bonusFloor']*maxpoints :
        #  bonus=1
        
        #totalreward=float(totalreward*EGParameters['numGames'])/float(EGParameters['maxgames'])
        ratio=float(maxpoints)/float(EGParameters['maxpoints_for_10_games'])
        #print 'totalreward : '+str(totalreward)+' ratio : '+str(ratio)
        if totalreward>=1*ratio and totalreward<=49*ratio:
          bonus="0.02"
        elif totalreward>=50*ratio and totalreward<=99*ratio:
          bonus="0.05"
        elif totalreward>=100*ratio and totalreward<=199*ratio:
          bonus="0.10"
        elif totalreward>=200*ratio and totalreward<=299*ratio:
          bonus="0.20"
        elif totalreward>=300*ratio:
          bonus="0.50"
        
      # end calculation continuous 08/03/2016
      
    part.status = Participant.COMPLETED
    user.endhit = datetime.now()
    db_session.add(user)
    db_session.commit()
    
    #rewardCode = ''
    for code in user.codes:
        if code.status==Code.FREE:
            #rewardCode = code.value
            code.status=Code.USED
            db_session.commit()
            break
    # 23032015
    
    if EGParameters['keyCodeMode']=='y':
      query_rs_keyCode= "update keycode_gameset_user set status='USED',totalreward="+str(totalreward)+",bonus='"+bonus+"'"+\
                        " where userid="+workerId+" and gamesetid="+assignmentId
      
      engine.execute(query_rs_keyCode)
      #print 'workerId=',workerId,'assignmentId',assignmentId
      try : # an "internal error" had occured one time during a gameset when selecting the keyCodeEnd, so we check for the exception
        query_rs_keyCode= "select keyCodeEnd from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
        rs_keyCode=engine.execute(query_rs_keyCode)
        row_rs_keyCode=rs_keyCode.fetchone()
        keyCodeEnd=row_rs_keyCode['keyCodeEnd']
      except :
        keyCodeEnd='';
    email=user.email
    if email==None:
      email=''
    errorsize='0'
    if workerId in gamesetsRunningList[assignmentId]['users']: # not a robot
      errorsize=str(gamesetsRunningList[assignmentId]['users'][workerId]['errorsize'])
        
    # rank of the workerId in the whole classement
    query_rs="SELECT workerId, round(avg( abs( decisions.value - image.percent ) / ( IF( pic_type = 'fractal', 1, 5 ) ) )) AS moy FROM choices, decisions, image WHERE choices.id = decisions.choiceid AND decisions.imageid = image.id GROUP BY workerId ORDER BY moy"
    rs=engine.execute(query_rs)
    workernum=0
    posofworkerId=0
    for row_rs in rs:
      workernum=workernum+1
      if(int(workerId)==int(row_rs['workerId'])):
        posofworkerId=workernum
    rank=str(100-int((float(posofworkerId)/float(workernum))*100))

    totalreward=str(int(totalreward))
    if totalreward=="":
      totalreward="0"
    
    return render_template('/eg/debriefing.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId, totalreward=totalreward, maxpoints=maxpoints, bonus=bonus, rank=rank,rewardcode=keyCodeEnd,email=email,EGParameters=EGParameters,htmltable=htmltable)

@app.route('/eg/completed', methods=['POST', 'GET'])
def completed():
    """
    This is sent when the participant completes the debriefing. The
    participant can accept the debriefing or declare that they were not
    adequately debriefed, and that response is logged in the database.
    """
    keyCodeEnd='';
    bonus=''
    
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    agreed=""
    if request.form.has_key('agree'):    
      agreed = request.form['agree']
    if request.form.has_key('email'):
      email = request.form['email']
      user.email = email
      db_session.commit()
    if request.form.has_key('note'):
      note = request.form['note']
      user.note = note
      db_session.commit()
    
    part = Participant.query.\
            filter(Participant.assignmentId == assignmentId).\
            filter(Participant.workerId == workerId).\
            one()
    part.status = Participant.DEBRIEFED
    part.debriefed = agreed == 'true'    
    db_session.add(part)
    db_session.commit()
    
    # 23032015
    if EGParameters['keyCodeMode']=='y':
      try : # an "internal error" had occured one time during a gameset when selecting the keyCodeEnd, so we check for the exception
        query_rs= "select keyCodeEnd,bonus from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
        rs=engine.execute(query_rs)
        row_rs=rs.fetchone()
        keyCodeEnd=row_rs['keyCodeEnd']
        bonus=row_rs['bonus']
      except :
        keyCodeEnd='';
        bonus=''
    # 26092016
    gameset = part.gamesets[0];#gamesets[0] is the unique gameset of a participant
    query_rs="select games.num as numgame, image.id as imageid, percent as goodresponse"+\
             " from games, image"+\
             " where image.gameid=games.id"+\
             " and games.gamesetid="+str(gameset.id)+\
             " order by games.num asc, image.id asc"
    rs=engine.execute(query_rs)
    tab_goodresponse=dict()
    numgame=-1
    for row_rs in rs:
      if row_rs['numgame']!=numgame :
        numgame=int(row_rs['numgame'])
        tab_goodresponse[row_rs['numgame']]=dict()
        numcolumn=1
      if numcolumn<=EGParameters['columnNumber']:
        tab_goodresponse[numgame][numcolumn]=row_rs['goodresponse']
        numcolumn=numcolumn+1
    
    tab_userdecision=dict()
    if workerId in gamesetsRunningList[assignmentId]['users']: # not a robot
      tab_userdecision=gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision']
    
    tab_influencability=dict()
    if EGParameters['playMode']=='discrete':
       tab_influencability=influencability(assignmentId,workerId)
       
    # 15102016 list of last decision in each game :  
    query_rs="select choices.workerid as workerid,games.num as gamenum,"+\
             " decisions.num as decisionnum,decisions.value as decisionval"+\
             " from decisions, choices, rounds, games"+\
             " where decisions.choiceid=choices.id and choices.roundid=rounds.id"+\
             " and rounds.gameid=games.id and rounds.num="+str(EGParameters['numRounds'])+" and decisions.num<"+str(EGParameters['columnNumber'])+\
             " and choices.assignmentid='"+str(assignmentId)+"'"+\
             " order by gamenum,decisionnum,workerid,decisions.timestamp asc"
    rs=engine.execute(query_rs)
    tab_game_lastdecision=dict()
    prev_decisionnum=-1
    for gamenum in range(1,EGParameters['numGames']+1):
      tab_game_lastdecision[gamenum]=dict()
      for decisionnum in range(0,EGParameters['columnNumber']):
        tab_game_lastdecision[gamenum][decisionnum+1]=dict()
    for row_rs in rs:
      if row_rs['decisionnum']!=prev_decisionnum :
        prev_decisionnum=row_rs['decisionnum']
      if(EGParameters['imageType']=='fractal') :
        tab_game_lastdecision[row_rs['gamenum']][row_rs['decisionnum']+1][row_rs['workerid']]=row_rs['decisionval']
      else:
        tab_game_lastdecision[row_rs['gamenum']][row_rs['decisionnum']+1][row_rs['workerid']]=int(row_rs['decisionval'])
      #print str(row_rs['gamenum'])+' '+str(row_rs['decisionnum']+1)+' '+str(row_rs['workerid'])+' : '+str(row_rs['decisionval'])
    #return render_template('/eg/completed.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId,EGParameters=EGParameters)
    return render_template('/eg/completed.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId,gameset_pic_name=gameset.pic_name,
                            tab_userdecision=tab_userdecision,tab_goodresponse=tab_goodresponse,tab_game_lastdecision=tab_game_lastdecision,
                            tab_influencability=tab_influencability, bonus=bonus, rewardcode=keyCodeEnd,EGParameters=EGParameters)
    # 26092016
    """return ('', 204)
     20160503
    return render_template('/eg/login.html',imageType=EGParameters['imageType'],loginValues=loginValues,EGParameters=EGParameters)
    20160503""" 

# 05102016
def influencability(assignmentId,workerId):
  # union add a line at the end of the rs in order to treat the last round of the last game
  query_rs="select choices.workerid as workerid,games.num as gamenum,"+\
           "rounds.num as roundnum,rounds.type as roundtype,decisions.num as decisionnum,decisions.status, decisions.value as decisionval"+\
           " from decisions, choices, rounds, games"+\
           " where decisions.choiceid=choices.id and choices.roundid=rounds.id"+\
           " and rounds.gameid=games.id"+\
           " and choices.assignmentid='"+str(assignmentId)+"'"+\
           " union select 0 as workerid, 1000 as gamenum, 1000 as roudnum, 0 as roundtype, 0 as decisionnum, 0 as status, 1000 as decisionval from decisions"+\
           " order by gamenum,roundnum,decisionnum"
  rs=engine.execute(query_rs)
  prev_roundnum=-1
  prev_gamenum=-1
  prev_roundtype=Round.LONE
  number_of_workerid_decisions=0 #count of decisions in the game for workerId
  sum_of_decision_values=0
  #num_influencability=0
  tab_lastdecision=dict()
  tab_average=dict()
  #tab_influencability=dict()
  list_influencability=list()
  for roundnum in range(1,EGParameters['numRounds']+2):
    tab_lastdecision[roundnum]=dict()
    for decisionnum in range(0,EGParameters['columnNumber']):
      tab_lastdecision[roundnum][decisionnum]=dict()
      #print 'roundnum '+str(roundnum)+' decisionnum '+str(decisionnum)
  
  for row_rs in rs :
    if prev_roundnum!=row_rs['roundnum'] and prev_roundnum!=-1:
      if row_rs['roundnum']!=1:# not useful for previous game last round 
        for decisionnum in range(0,EGParameters['columnNumber']):
          sum_of_decision_values=0
          number_of_workerid_decisions=0
          line='roundnum '+str(row_rs['roundnum'])
          for a_workerid in tab_lastdecision[prev_roundnum][decisionnum]:
            decision=tab_lastdecision[prev_roundnum][decisionnum][a_workerid]
            line=line+' '+str(decision['decisionval'])
            if decision['status']==Decision.USER_MADE:
              sum_of_decision_values=sum_of_decision_values+decision['decisionval']
              number_of_workerid_decisions=number_of_workerid_decisions+1
          line=line+' average : '
          if number_of_workerid_decisions!=0:
            tab_average[decisionnum]=sum_of_decision_values/number_of_workerid_decisions
            line=line+str(tab_average[decisionnum])
          #print line
      if row_rs['roundnum']!=2:
        for decisionnum in range(0,EGParameters['columnNumber']):
          # print 'prev_roundnum-1 '+str(prev_roundnum-1)+' decisionnum '+str(decisionnum)
          d2=tab_lastdecision[prev_roundnum-1][decisionnum][str(workerId)]
          d1=tab_lastdecision[prev_roundnum][decisionnum][str(workerId)]
          if tab_average[decisionnum]-d2['decisionval']!=0 and tab_average[decisionnum]!=0 and d1['status']==Decision.USER_MADE and d2['status']==Decision.USER_MADE:
            influencability=(d1['decisionval']-25-d2['decisionval'])/(tab_average[decisionnum]-d2['decisionval'])
            list_influencability.append(influencability)
            # print 'd1 '+str(d1['decisionval'])+' d2 '+str(d2['decisionval'])+' tab_average[decisionnum] '+str(tab_average[decisionnum])
            # print 'tab_influencability[num_influencability] '+str(influencability)
            # not registered if infini
            #num_influencability=num_influencability+1
    if row_rs['gamenum']!=1000 : # last rs line from the union select
      prev_roundnum=row_rs['roundnum']
      tab_lastdecision[row_rs['roundnum']][row_rs['decisionnum']][row_rs['workerid']]=row_rs

  list_influencability.sort()
  #print list_influencability
  influencability_coefficient=median(list_influencability)
  if influencability_coefficient<=0.1:
    influencability_text='you are very stubborn'
  elif influencability_coefficient<=0.2:
    influencability_text='you are stubborn'
  elif influencability_coefficient<=0.3:
    influencability_text='you are just a little stubborn'
  else:
    influencability_text='you are not stubborn'
  return {'influencability_coefficient':round(influencability_coefficient,2),'influencability_text':influencability_text}

  
# 12092016
@app.route('/eg/stop_the_gameset', methods=['POST', 'GET'])
def stop_the_gameset():
    keyCodeEnd='';
    bonus=''
    
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    if request.method == 'POST':
      if EGParameters['keyCodeMode']=='y':
        query_rs= "update keycode_gameset_user set status='USED',totalreward=0,bonus='"+str(EGParameters['stop_the_gameset_no_other_participant_bonus'])+"'"+\
                  " where userid="+workerId+" and gamesetid="+assignmentId
        engine.execute(query_rs)
        try : # an "internal error" had occured one time during a gameset when selecting the keyCodeEnd, so we check for the exception
          query_rs= "select keyCodeEnd,bonus from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
          rs=engine.execute(query_rs)
          row_rs=rs.fetchone()
          keyCodeEnd=row_rs['keyCodeEnd']
          bonus=row_rs['bonus']
        except :
          keyCodeEnd='';
          bonus=''
      return render_template('/eg/completed_stopped.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId,
                              bonus=bonus, rewardcode=keyCodeEnd, EGParameters=EGParameters)
                              
    elif (request.args.has_key('getFlag')):
      elapsedTime=(datetime.utcnow()-gamesetsRunningList[assignmentId]['stop_the_gameset_no_other_participant_time']).total_seconds()
      #print elapsedTime
      # if elapsedTime< EGParameters['stop_the_gameset_no_other_participant_delay_to_agree']:
      remainingTime=EGParameters['stop_the_gameset_no_other_participant_delay_to_agree']-elapsedTime
      return json.dumps({'hitId': hitId,'assignmentId': assignmentId,'workerId': workerId,'sessionId':user.sessionId,'remainingTime':int(remainingTime)})
      #else:
        # return render_template('/eg/completed.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId,EGParameters=EGParameters)  
    else:
      return render_template('/eg/stop_the_gameset.html', hitId = hitId, assignmentId=assignmentId, sessionId=user.sessionId, workerId=workerId, EGParameters=EGParameters)

# 12092016
@app.route('/eg/completed_stopped', methods=['POST', 'GET'])
def completed_stopped():
    keyCodeEnd='';
    bonus=''
    
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    
    if EGParameters['keyCodeMode']=='y':
      try : # an "internal error" had occured one time during a gameset when selecting the keyCodeEnd, so we check for the exception
        query_rs= "select keyCodeEnd,bonus from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
        rs=engine.execute(query_rs)
        row_rs=rs.fetchone()
        keyCodeEnd=row_rs['keyCodeEnd']
        bonus=row_rs['bonus']
      except :
        keyCodeEnd='';
        bonus=''
    return render_template('/eg/completed_stopped.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId,
                            bonus=bonus, rewardcode=keyCodeEnd,EGParameters=EGParameters)

@app.route('/eg/session_has_expired', methods=['POST', 'GET'])
def session_has_expired():
   return render_template('/eg/session_has_expired.html')

# 12092016
#----------------------------------------------
# generic route
#----------------------------------------------
@app.route('/eg/<pagename>')
def regularpage(pagename=None):
    # Route not found by the other routes above. May point to a static template.
    if pagename==None:
        raise ExperimentError('page_not_found')
    return render_template(pagename)


#----------------------------------------------
# functions added by sam - June 2013
#----------------------------------------------
@app.route('/eg/<pagename>')
def link_participant_to_game(user):
    currentWaitingGames = Game.query.filter(Game.status == Game.WAITING_FOR_PARTICIPANTS);
    if(user.game != None):
        print "user is already in a game"
        raise ExperimentError('user_already_in_game');
    elif(currentWaitingGames.count()>0):
        game = currentWaitingGames.one();
    else: 
        game = Game(EGParameters);
        db_session.add(game);
    game.participants.append(user);
    if(game.participants.count()==game.numExpectedParticipants):
        game.status = game.STARTED;
    user.games.append(game);
    db_session.commit();
    return game

#----------------------------------------------
# Monitoring route
#----------------------------------------------
@app.route('/eg/monitor', methods=['GET','POST'])
def monitor():
  global adminSessionId
  global adminState
  EGDBContent=dict();
  error="You have to connect before!"#default
  if request.values.has_key('sessionId'):
    if request.values['sessionId']==adminSessionId :
      if request.method == 'POST':
        if request.values.has_key('newstatusvalue') and request.values.has_key('keyCodeBegin'):
          query_rs="update keycode_gameset_user set status="+GetSQLValueString(request.values['newstatusvalue'], 'text')+\
                    ",resultpaycode="+GetSQLValueString('MANUAL', "text")+\
                    ",resultpaymessage="+GetSQLValueString('', "text")+\
                    " where keyCodeBegin="+GetSQLValueString(request.values['keyCodeBegin'], 'text')
          engine.execute(query_rs)
        elif request.values.has_key('clean_tables_after_end_on_start'):
          clean_tables_after_end_on_start()
        """elif request.values.has_key('dump_db'):
          print 'dump_db'
          dump_db(EGParameters['tmpPath'])
        """
      EGDBContent=get_db_keys_users_gamesets();
      error=''
  return render_template('/eg/monitor.html',sessionId=adminSessionId,error=error,adminState=adminState, EGParameters=EGParameters,EGDBContent=EGDBContent)

@app.route('/eg/result', methods=['GET'])
def result():
  global adminSessionId
  global adminState
  what=''
  res=''
  period=''
  datebegin=''
  dateend=''
  if request.values.has_key('sessionId'):
    if request.values['sessionId']==adminSessionId :  
      if request.values.has_key('what'):
        what=request.values['what']
        if request.values.has_key('datebegin'):
          datebegin=request.values['datebegin']
        if request.values.has_key('dateend'):
          dateend=request.values['dateend'] 
        if what=='db_get_decision' :
          res=db_get_decision(datebegin,dateend)
        elif what=='db_get_user' :
          res=db_get_user(datebegin,dateend)
        elif what=='db_get_free_keys':
          res=db_get_free_keys()
  return Response(res,mimetype='text/plain')
   
#----------------------------------------------
# Administration route
#----------------------------------------------
@app.route('/eg/admin', methods=['GET','POST'])  
def admin():
  global adminSessionId
  global adminState
  global connection
  connection = engine.connect()
  db_users_gamesets=dict()
  numFreeKeyCode=""
  loginError = ''
  warning=''
  content=dict()
  """if not request.values.has_key('getFlag'):
    print request.method+' parameters'
    for key in request.values:
      print request.values[key]
    print 'end parameters'"""
  if request.values.has_key('sessionId'):
    if request.values['sessionId']==adminSessionId :
      adminState='logged';
      if request.method == 'POST':
        if request.form.has_key('submitlogout'):
          adminSessionId=''
          adminState=''
          loginError=''
        else :
          EGParameters['cwf_displaying_payment']='n'
          if request.form.has_key('submitstop') :
            EGParameters['EGRunning']=False;
            gamesetsRunningList=dict();
          elif request.form.has_key('submitpreviewpay') :
            if EGParameters['job_id']!='':
              content=view_participants_of_a_job_id(EGParameters)
              EGParameters['cwf_displaying_payment']='y'
          elif request.form.has_key('submitpay') :
            if EGParameters['job_id']!='':
              pay_participants(EGParameters)
              content=view_participants_of_a_job_id(EGParameters)
              EGParameters['cwf_displaying_payment']='y'
          elif request.form.has_key('submitstart') :
            nowDate = datetime.utcnow()
            EGParameters['starttimeutc']=nowDate
            try :
              if request.form.has_key('job_id') :
                EGParameters['job_id']=string.strip(request.form['job_id'])
                if request.form.has_key('pay_platform') :
                  EGParameters['pay_platform']=request.form['pay_platform']
                  #print EGParameters['pay_platform']
                  if EGParameters['pay_platform']=='cwf':
                    EGParameters['keyCodeMode']='y'
              if request.form.has_key('activateTimer') :
                EGParameters['activateTimer']='y'
              else:
                EGParameters['activateTimer']='n'
              if request.form.has_key('useExistingGames'):
                EGParameters['useExistingGames']='y'
                EGParameters['addRobotsMode']='y'
                EGParameters['checkIP']='n'
                EGParameters['numExpectedParticipants']=6
                EGParameters['numRounds']=3
              else:
                EGParameters['useExistingGames']='n'
                if request.form.has_key('addRobotsMode'):
                  EGParameters['addRobotsMode']='y'
                  EGParameters['checkIP']='n'
                else:
                  EGParameters['addRobotsMode']='n'
              if request.form.has_key('redundantMode') :
                EGParameters['redundantMode']='y'
              else:
                EGParameters['redundantMode']='n'
              if request.form.has_key('withPassword') :
                EGParameters['withPassword']='y'
              else:
                EGParameters['withPassword']='n'
              if request.form.has_key('keyCodeMode') :
                EGParameters['keyCodeMode']='y'
              else:
                EGParameters['keyCodeMode']='n'
              
              if EGParameters['job_id']!='' and EGParameters['pay_platform']=='cwf':
                EGParameters['keyCodeMode']='y'
              
              if request.form.has_key('checkIP') and not EGParameters['addRobotsMode']=='y':
                EGParameters['checkIP']='y'
              else:
                EGParameters['checkIP']='n'
              if request.form.has_key('starthour'):
                try:
                  if EGParameters['activateTimer']=='y' :
                    EGParameters['starthour']=request.form['starthour']
                  else :
                    EGParameters['starthour']='0:0'
                  EGParameters['nextGameDate']=nowDate+timedelta(hours=int(list(split(EGParameters['starthour'],':'))[0]),minutes=int(list(split(EGParameters['starthour'],':'))[1]))
                except:
                  warning=warning+'Experiment time malformed hh:mn'
              if request.form.has_key('maxDelayToLoginGameSet') :
                try:
                  EGParameters['maxDelayToLoginGameSet']=int(request.form['maxDelayToLoginGameSet'])
                except:
                  warning=warning+'Max delay to log... not int.'
              if request.form.has_key('maxDelayToBeginGameSet') :
                try:
                  EGParameters['maxDelayToBeginGameSet']=int(request.form['maxDelayToBeginGameSet'])
                except:
                  warning=warning+'Max delay to begin... not int.'
              if request.form.has_key('position_or_value') :
                EGParameters['position_or_value']=request.form['position_or_value']

              if request.form.has_key('imageType') :
                EGParameters['imageType']=request.form['imageType']
                if EGParameters['imageType'] == 'fractal' :
                  EGParameters['bonusFloor']=0.5
                elif EGParameters['imageType'] == 'peanut' :
                  EGParameters['bonusFloor']=0.33
                  
              if EGParameters['position_or_value']=='value' :
                EGParameters['displayedimgsize']=EGParameters['imgsize']# 20160204
                if EGParameters['imageType'] == 'fractal' :
                  EGParameters['minDecisionValue']='0.0'
                  EGParameters['maxDecisionValue']='100.0' 
                elif EGParameters['imageType'] == 'peanut' :
                  EGParameters['minDecisionValue']='0'
                  EGParameters['maxDecisionValue']='500'
              else :
                EGParameters['minDecisionValue']='0'
                EGParameters['maxDecisionValue']=EGParameters['imgsize']
                EGParameters['displayedimgsize']=str(int(EGParameters['imgsize'])*1.3)# 20160204
              ## end if
              if request.form.has_key('numRounds') and not EGParameters['addRobotsMode']=='y':
                try:
                  EGParameters['numRounds']=int(request.form['numRounds'])
                except:
                  warning=warning+'Rounds... not int.'
              if request.form.has_key('numGames') :
                try:
                  EGParameters['numGames']=int(request.form['numGames'])
                except:
                  warning=warning+'Games... not int.'
              if request.form.has_key('numImages') :
                try:
                  EGParameters['numImages']=int(request.form['numImages'])
                except:
                  warning=warning+'numImages... not int. or images generation problem'
              if request.form.has_key('playMode') :
                EGParameters['playMode']=request.form['playMode']
                if EGParameters['playMode']=='discrete' :
                  EGParameters['columnNumber']=3
                  EGParameters['numRounds']=3
                  EGParameters['graduationRuleWidth']=250
                  EGParameters['graduationRuleWidthZoom']=2000
                  EGParameters['loneMaxReward']=15
                  EGParameters['socialMaxReward']=30
                else :#continuous
                  EGParameters['columnNumber']=1
                  EGParameters['numRounds']=2
                  EGParameters['graduationRuleWidth']=1000
                  EGParameters['graduationRuleWidthZoom']=4000
                  EGParameters['loneMaxReward']=1
                  EGParameters['socialMaxReward']=EGParameters['socialRoundDuration']              

              if request.form.has_key('loneRoundDuration') :
                try:
                  EGParameters['loneRoundDuration']=int(request.form['loneRoundDuration'])
                except:
                  warning=warning+'Duration... not int.'
              if request.form.has_key('socialRoundDuration') :
                try:
                  EGParameters['socialRoundDuration']=int(request.form['socialRoundDuration'])
                except:
                  warning=warning+'Duration... not int.'
              
              EGParameters['ratioForErrorSize']=(float(EGParameters['maxDecisionValue'])-float(EGParameters['minDecisionValue']))/100
              
              if request.form.has_key('numExpectedParticipants') and not EGParameters['useExistingGames']=='y':
                try:
                  EGParameters['numExpectedParticipants']=int(request.form['numExpectedParticipants'])
                except:
                  warning=warning+'Participants... not int.'
                  EGParameters['numExpectedParticipants']=6
              else:
                EGParameters['numExpectedParticipants']=6
              # 19082016
              if request.form.has_key('forceStartAfterWait'):
                EGParameters['forceStartAfterWait']='y'
              else :
                EGParameters['forceStartAfterWait']='n'
              
              if request.form.has_key('forceStartAfterWaitDelay'):
                EGParameters['forceStartAfterWaitDelay']=int(request.form['forceStartAfterWaitDelay'])
              else :
                EGParameters['forceStartAfterWaitDelay']=''
              
              if request.form.has_key('forceStartAfterWaitNumParticipants'):
                EGParameters['forceStartAfterWaitNumParticipants']=int(request.form['forceStartAfterWaitNumParticipants'])
              else :
                EGParameters['forceStartAfterWaitNumParticipants']=''
                
              if request.form.has_key('stop_the_gameset_no_other_participant'):
                EGParameters['stop_the_gameset_no_other_participant']='y'
              else :
                EGParameters['stop_the_gameset_no_other_participant']='n'
              
              if request.form.has_key('stop_the_gameset_no_other_participant_delay'):
                EGParameters['stop_the_gameset_no_other_participant_delay']=int(request.form['stop_the_gameset_no_other_participant_delay'])
              else :
                EGParameters['stop_the_gameset_no_other_participant_delay']=''
              
              if request.form.has_key('stop_the_gameset_no_other_participant_delay_to_agree'):
                EGParameters['stop_the_gameset_no_other_participant_delay_to_agree']=int(request.form['stop_the_gameset_no_other_participant_delay_to_agree'])
              else :
                EGParameters['stop_the_gameset_no_other_participant_delay_to_agree']=''
              
              if request.form.has_key('stop_the_gameset_no_other_participant_bonus'):
                EGParameters['stop_the_gameset_no_other_participant_bonus']=float(request.form['stop_the_gameset_no_other_participant_bonus'])
              else :
                EGParameters['stop_the_gameset_no_other_participant_bonus']=''
              # 20092016
              
              if request.form.has_key('skipConsentInstruct'):
                EGParameters['skipConsentInstruct']='y'
                EGParameters['skipQuestionnaire']='y'
              else:
                EGParameters['skipConsentInstruct']='n'
                if request.form.has_key('skipQuestionnaire'):
                  EGParameters['skipQuestionnaire']='y'
                else:
                  EGParameters['skipQuestionnaire']='n'
              if request.form.has_key('numNewKeyCodes'):
                try:
                  EGParameters['numNewKeyCodes']=int(request.form['numNewKeyCodes'])
                except:
                  warning=warning+'Key codes... not int.'
              ## end if
              if EGParameters['useExistingGames']=='y' and not check_for_enough_games(EGParameters) :
                warning='Not enough games in existing "good games" to start!'  
              if warning=='':
                clean_tables_after_end_on_start()
                EGParameters['EGRunning']=True;
                generateImages(EGParameters)
                if request.form.has_key('freeImages') and request.form['freeImages']=='y' :
                  free_images()
                if(EGParameters['numNewKeyCodes'])>0:
                  generateNewKeyCodes(EGParameters['numNewKeyCodes'])
                #201411 continuousListOfChoices=[]
                #201411 continuous_list_of_decisions_of_a_participant=[]
            except:#a warning to explain
              sysexc_info=sys.exc_info()
              warning=warning+str(sysexc_info[1])
      ## end if POST
    else:
      loginError = 'Invalid session Id or not connected'
      adminState='loginError';
  else :
    if request.method == 'POST':
      if request.form.has_key('username') and request.form.has_key('pwd') :
        if request.form['username']=='cran' and request.form['pwd']=='cr,,an':
          adminSessionId = str(random.randint(10000000, 99999999));
          adminState='logged';
        else :
          loginError = 'Invalid username/password'
          adminState='loginError';
      else :
        loginError = 'Not logged in'
        adminState='loginError';
    else :
      adminState='';
      
  # we continue the procedure here with correct adminState='logged'
  # It's to go out from the multiple if-else above and get a more readable code :-)
  if adminState=='':
      return render_template('/eg/admin.html',adminState=adminState)
  elif adminState=='loginError':
      return render_template('/eg/admin.html',adminState=adminState,loginError=loginError)
  elif adminState=='logged':
    if(request.args.has_key('getFlag')):
      timeLeft=0
      loginState=''
      gameSetState=''
      nowDate = datetime.utcnow()
      timerValue=(nowDate-EGParameters['nextGameDate']).total_seconds()
      if(timerValue<0):
        loginState='beforeLogin'
        gameSetState='beforeRunning'
        timeLeft=abs(int(timerValue))
      else:
        loginState='openLogin'
        gameSetState='Running'
        timeLeft=abs(int(timerValue)-EGParameters['maxDelayToLoginGameSet']*60)
        if(timerValue-EGParameters['maxDelayToLoginGameSet']*60>0):
          loginState='closeLogin'
          timeLeft=0
          gameSetDuration=EGParameters['numGames']*(EGParameters['loneRoundDuration']+EGParameters['socialRoundDuration']*(EGParameters['numRounds']-1))    
          if(timerValue-EGParameters['maxDelayToBeginGameSet']*60-gameSetDuration>0):
              gameSetState='afterRunning'
      #print get_EG_session_info(EGParameters)
      adminAttributes={'EGRunning':EGParameters['EGRunning'],
                        'job_id':EGParameters['job_id'],
                        'activateTimer':EGParameters['activateTimer'],
                        'loginState':loginState,
                        'timeLeft':str((timeLeft)//60)+'mn '+str((timeLeft)%60),
                        'gameSetState':gameSetState,
                        'EG_session_info':get_EG_session_info(EGParameters),
                        'cwf_displaying_payment':EGParameters['cwf_displaying_payment']
                       }
      return json.dumps(adminAttributes)
    else:
      EGParameters['totalImagesNumber']=Image.query.filter(Image.status == Image.FREE or Image.status == Image.USED).count();
      EGParameters['freeImagesNumber']=Image.query.filter(Image.status == Image.FREE).count();
      EGParameters['totalfractalImagesNumber']=Image.query.filter(Image.pic_type=='fractal').count();
      EGParameters['totalpeanutImagesNumber']=Image.query.filter(Image.pic_type=='peanut').count();
      EGParameters['freefractalImagesNumber']=Image.query.filter(Image.status == Image.FREE,Image.pic_type=='fractal').count();
      EGParameters['freepeanutImagesNumber']=Image.query.filter(Image.status == Image.FREE,Image.pic_type=='peanut').count();
      query_rs= "select count(*) as count from keycode_gameset_user where userid=-1 and gamesetid=-1"
      rs=engine.execute(query_rs)
      row_rs=rs.fetchone()
      numFreeKeyCode=row_rs['count']
      #print adminSessionId,' ',adminState,' ',loginError,' ',warning
      return render_template('/eg/admin.html',adminState=adminState, sessionId=adminSessionId,warning=warning,
                              EGParameters=EGParameters,numFreeKeyCode=numFreeKeyCode,content=content)
   
#----------------------------------------------
# robot_controler route : wakes up the mysql server
#----------------------------------------------
@app.route('/eg/robot_controler', methods=['GET','POST'])  
def robot_controler():
  if request.values.has_key('pwd') and request.values['pwd']=='pwdrobot_controler' :
    #try: 
      game = db_session.query(Game).filter(Game.num==1).first();
      return 'game'
    #except:
      #return 'robot_controler exception'
      
  
def generateImages(EGParameters):
  # generate EGParameters['numImages'] images and store them in the database
  i=0
  for i in  range(1,EGParameters['numImages']+1):#range(1,numImages+1)
    if EGParameters['imageType'] == 'fractal' :
      pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
      out = fractale_complex(EGParameters['estimationPicPath'],pic_name)
      img = Image(pic_name,out[0],out[1],out[2],EGParameters['imageType'])
    else :
      pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
      nbpeanuts = peanuts_light(float(random.randint(200,480))/800,EGParameters['picPath'],EGParameters['estimationPicPath'],pic_name);
      img = Image(pic_name,nbpeanuts,'',0,EGParameters['imageType'])
    db_session.add(img)
    db_session.commit()
    
# 11/03/2015
def create_and_select_redundant_images(EGParameters,gamesetid):
  gameset_pic_list=[]
  tab_of_pic=dict()
  image_ordered_list_file=open(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+'/image_ordered_list.csv'))
  numgame=1
  for a_line in image_ordered_list_file:
    game = Game(EGParameters);
    game.num = numgame;
    game.numExpectedParticipants = EGParameters['numExpectedParticipants'];
    game.numRounds=EGParameters['numRounds'];
    game.gamesetid=gamesetid
    db_session.add( game )
    db_session.commit()
    game_pic_list=[]
    an_ordered_line=a_line.strip("\n")
    index_list=an_ordered_line.split(",")
    for index in index_list:
      index=index.strip()
      if not index in tab_of_pic:
        if EGParameters['imageType'] == 'fractal' :
          pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
          out = fractale_complex(EGParameters['estimationPicPath'],pic_name)
          img = Image(pic_name,out[0],out[1],out[2],EGParameters['imageType'])
        else :
          pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
          nbpeanuts = peanuts_light(float(random.randint(200,480))/800,EGParameters['picPath'],EGParameters['estimationPicPath'],pic_name);
          img = Image(pic_name,nbpeanuts,'',0,EGParameters['imageType'])
        tab_of_pic[index]=img
      else :
        imgtocopy=tab_of_pic[index]
        img = Image(imgtocopy.pic_name,imgtocopy.percent,imgtocopy.color,imgtocopy.complexity,imgtocopy.pic_type)
      img.status=Image.USED
      img.gameid=game.id
      db_session.add(img)
      db_session.commit()
      game_pic_list.append(tab_of_pic[index].pic_name)
    gameset_pic_list.append(game_pic_list)    
    numgame=numgame+1
  return gameset_pic_list
# end 11/03/2015

#----------------------------------------------------------
# Variables and default values
#----------------------------------------------------------

parser = argparse.ArgumentParser(description='Estimation game')
parser.add_argument('-p','--serverPort',  help='Application http port (default='+str(SERVER_PORT)+')', default=SERVER_PORT)
parser.add_argument('-hp','--httpPort',  help='httpPort for local robots (default=80)', default=80)
parser.add_argument('-i','--initDatabase', choices=['y', 'n'],  help='Initialize database (default=n)', default='n')
args = parser.parse_args()
# useExistingGames : replay a gameset for a user and robots
# robots decisions come from existing games
# addRobotsMode : add robots in a gameset to complete the human users

EGParameters = dict(EGRunning=False,initDatabase=args.initDatabase,serverPort=args.serverPort,httpPort=args.httpPort,playMode='continuous',
position_or_value='value', imgsize='200',
imageType = 'peanut',freeImages='n',numImages=0,loneRoundDuration=20,socialRoundDuration=20,loneMaxReward=15,socialMaxReward=30,
numExpectedParticipants=6,maxgames=10,numGames=1,numRounds=2,numNewKeyCodes=1,testMode='n',skipConsentInstruct='y',skipQuestionnaire='n',
keyCodeMode='y',withPassword='n',activateTimer='n',starthour='0:10',maxDelayToLoginGameSet=4,maxDelayToBeginGameSet=10,
checkIP='n',useExistingGames='n',addRobotsMode='y', redundantMode='n',database=DATABASE_NAME,
# 19082016
forceStartAfterWait='n', forceStartAfterWaitDelay=2,forceStartAfterWaitNumParticipants=2,
# 19082016
# 12092016
stop_the_gameset_no_other_participant='n',
stop_the_gameset_no_other_participant_delay=1,stop_the_gameset_no_other_participant_delay_to_agree=20,
stop_the_gameset_no_other_participant_bonus='0.02',
job_id='',#930744
cwf_api_key = 'vir74DJsY4m5Jz6BwcM-',
cwf_timeout=30,
bonusmax='1',# max amount to pay
cwf_displaying_payment='n',
pay_platform='test',
decision_out_of_limit_time=5 # to take in account decisions submitted during the duration of a round but not received after this duration
);
EGParameters['maxpoints_for_10_games']=EGParameters['maxgames']*(EGParameters['socialRoundDuration']+EGParameters['decision_out_of_limit_time'])
print EGParameters['maxpoints_for_10_games']
if(EGParameters['initDatabase']=='y') :
  confirm=raw_input('Are you sure (y/n):')
  if confirm=='y':
    init_db()
  else:
    print 'Database not initialized'
connection = engine.connect()


EGParameters['graduationRuleHeight']=60
EGParameters['graduationRuleHeightZoom']=60
if EGParameters['playMode']=='discrete' :
  EGParameters['columnNumber']=3
  EGParameters['graduationRuleWidth']=250
  EGParameters['graduationRuleWidthZoom']=2000
  EGParameters['loneMaxReward']=15
  EGParameters['socialMaxReward']=30

else :#continuous
  EGParameters['columnNumber']=1
  EGParameters['numRounds']=2
  EGParameters['graduationRuleWidth']=1000
  EGParameters['graduationRuleWidthZoom']=4000
  EGParameters['loneMaxReward']=1
  EGParameters['socialMaxReward']=EGParameters['socialRoundDuration']
  
if EGParameters['imageType'] == 'fractal' :
  EGParameters['bonusFloor']=0.5
elif EGParameters['imageType'] == 'peanut' :
  EGParameters['bonusFloor']=0.33

#EGParameters['numImages']=EGParameters['numGames']*EGParameters['columnNumber']
# EGParameters['site'] is used in admin.html to display "only on collective-intelligence (eg_open) site"
EGParameters['site']='eg'
if DATABASE_NAME[0:7]=="eg_open" :
  EGParameters['useExistingGames']='y'
  EGParameters['addRobotsMode']='y'
  EGParameters['skipConsentInstruct']='y'
  EGParameters['numGames']='3'
  EGParameters['numImages']=0
  EGParameters['EGRunning']=True
  EGParameters['site']='eg_open'
print 'database: ',DATABASE_NAME, 'site root: ',str(os.path.normpath(os.path.abspath(os.path.dirname(__file__))))
print 'useExistingGames: ',EGParameters['useExistingGames'], 'addRobotsMode: ',EGParameters['addRobotsMode']
EGParameters['staticPath']="/static/"
EGParameters['tmpPath']=EGParameters['staticPath']+"tmp/"
EGParameters['picPath'] = EGParameters['staticPath']+"pic/"# base pictures path
EGParameters['estimationPicPath'] = EGParameters['picPath']+"estimationPic/" # pictures for estimations
EGParameters['tmpPicPath']= EGParameters['picPath']+"tmp/"# pictures generated during rounds. They can be deleted after a game set
EGParameters['totalImagesNumber']=Image.query.filter(Image.status == Image.FREE or Image.status == Image.USED).count();
EGParameters['freeImagesNumber']=Image.query.filter(Image.status == Image.FREE).count();

EGParameters['displayedimgsize']=EGParameters['imgsize']# 20160204
if EGParameters['position_or_value']=='value' :
  if EGParameters['imageType'] == 'fractal' :
    EGParameters['minDecisionValue']='0.0'
    EGParameters['maxDecisionValue']='100.0' 
  elif EGParameters['imageType'] == 'peanut' :
    EGParameters['minDecisionValue']='0'
    EGParameters['maxDecisionValue']='500'
else :
    EGParameters['minDecisionValue']='0'
    EGParameters['maxDecisionValue']=EGParameters['imgsize']
    EGParameters['displayedimgsize']=str(int(EGParameters['imgsize'])*1.3)# 20160204
EGParameters['ratioForErrorSize']=(float(EGParameters['maxDecisionValue'])-float(EGParameters['minDecisionValue']))/100

nowDate = datetime.utcnow()
EGParameters['starttimeutc']=nowDate
EGParameters['nextGameDate']=nowDate+timedelta(hours=int(list(split(EGParameters['starthour'],':'))[0]),minutes=int(list(split(EGParameters['starthour'],':'))[1]))
loginAttributes={'EGRunning':EGParameters['EGRunning'],'timeLeftBeforeGameSet':(nowDate-EGParameters['nextGameDate']).total_seconds()}

# gamesetsRunningList contains informations that will not be registered in db 
gamesetsRunningList=dict();
adminSessionId=''
adminState=''
# perhaps some gamesets, users,... in the db have not been stopped properly : we "clean"   
clean_tables_after_end_on_start()
# to avoid the mysql server has gone : start a robot which 'wakes up' wsgi !!!
os.spawnl(os.P_NOWAIT, r'C:\Program Files (x86)\PHP\php','php', str(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+'/robot_eg_controler.php '))+str(EGParameters['httpPort']))

# print influencability(1,1)
# content=view_participants_of_a_job_id(EGParameters)
# for i in content:
  # row=content[i]
  # line=""
  # for field in row:
    # line=line+str(field)
  # print line

# print str(int((float("0"+"0.1")*100)))
if __name__ == '__main__':
    #try:
      app.run(host=SERVER_HOST, port=EGParameters['serverPort'], debug=SERVER_DEBUG)
    #except:
      #print 'app.run exception'