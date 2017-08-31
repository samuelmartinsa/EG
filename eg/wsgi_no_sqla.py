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
from db_no_sqla import connection, cursor,init_db,init_db_connection, free_images,generateNewKeyCodes,serious_workers_have_chosen,\
                get_db_keys_users_gamesets,db_get_free_keys, get_db_users_gamesets,db_get_decision,db_get_user,\
                clean_tables_after_end_on_start,GetSQLValueString,get_EG_session_info,dump_db,\
                select_and_create_games, check_for_enough_games, pay_participants, view_participants_of_a_job_id
from models_no_sqla import Participant, Game, GameSet, Round, Choice, Decision, User, Questionnaire, Image #,keycode_gameset_user
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
# @app.teardown_request
# def shutdown_session(exception=None):
    # db_session.remove()

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
@app.route('/eg/signup', methods=['GET'])
def signup():
    return render_template('/eg/signup.html')

@app.route('/eg/signupuser', methods=['POST'])
def signupuser():
    user =  request.form['username'];
    password = request.form['password'];
    return json.dumps({'status':'OK','user':user,'pass':password});
    
def check_session(user,session):
    #print "in check_session user.id ",user.id,"user.sessionId ",user.sessionId,"now()",datetime.now() 
    if(user.sessionId!=session or not user.lastvisit or (datetime.now() - user.lastvisit) > timedelta (minutes = 10)):         
        return False;
    else:
        user.lastvisit = datetime.now(); # update
        user.update()
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
        query="select * from keycode_gameset_user"+\
              " where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text")+\
              " and keycode_gameset_user.gamesetid not in (select id from gamesets where status="+GetSQLValueString(GameSet.TERMINATED, "text")+")"
        cursor.execute(query)
        if(cursor.rowcount==1):
          row=cursor.fetchone()
          userId_of_givenKeyCodeBegin=row['userid']
          gameSetId_of_givenCodeKeyCodeBegin=row['gamesetid']
        else:
          return render_template('/eg/login.html',flag="KEYCODE_NONEXISTANT_OR_USED",loginValues=loginValues,EGParameters=EGParameters);
      else:
        return render_template('/eg/login.html',flag="MISSING_KEYCODE",loginValues=loginValues,EGParameters=EGParameters);
    
    # key code exists in db and is not used in a terminated gameset
    # and (EGParameters['activateTimer']=='n' or loginState=='openLogin')
    # users and robots have to login :
    # - a user requests with 'loginsignin'="new" or "returning"
    # - a robot requests with  'loginsignin'="robot" : ip and keycode are not checked 
    if(request.form.has_key('username') and request.form.has_key('pwd') and request.form.has_key('loginsignin')):
      query="select count(*) as count from users where ipaddress='"+ipaddress+"'"# and ip_in_use='y'"
      cursor.execute(query);
      row=cursor.fetchone()
      if row['count']>=1 and EGParameters['checkIP']=='y':
        return render_template('/eg/login.html',imageType=EGParameters['imageType'],flag="IP_ALREADY_IN_DB",loginValues=loginValues,EGParameters=EGParameters);

      username = request.form['username'];
      password = request.form['pwd']
      if(request.form['loginsignin']=="new"):
        # Check if username exists in database
        query="select count(*) as matchesUser from users where username="+GetSQLValueString(username, 'text')
        cursor.execute(query);
        row=cursor.fetchone()
        if(row['matchesUser']==1):
          return render_template('/eg/login.html',flag="ALREADY_IN_DB",loginValues=loginValues,EGParameters=EGParameters);
        elif(row['matchesUser']==0):
          # check for existing IP address (this feature does not work yet because IP is not properly fetch and put in database)
          if(EGParameters['checkIP']=='y'):
            query="select count(*) as matchesIP from users where ipaddress="+GetSQLValueString(ipaddress, 'text')+" and ip_in_use='y'"
            cursor.execute(query);
            row=cursor.fetchone()
            if(row['matchesIP']>=1):
              return render_template('/eg/login.html',imageType=EGParameters['imageType'],flag="IP_ALREADY_IN_DB",loginValues=loginValues,EGParameters=EGParameters);
          if(userId_of_givenKeyCodeBegin!=-1 and EGParameters['keyCodeMode']=='y'): #already assigned to an other user
            return render_template('/eg/login.html',flag="KEYCODE_ALREADY_USED",loginValues=loginValues,EGParameters=EGParameters);
          user = NewUser(username,password,ipaddress)#
          user.ip_in_use='y'
          user.update()
          workerId = str(user.id);
          if EGParameters['keyCodeMode']=='y':
            cursor.execute("update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE', usagetime='"+str(datetime.now())+"' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text"))
            connection.commit()
          assignmentId = "0";
          hitId = "0";
          return render_template('/eg/consent.html',sessionId=user.sessionId, hitId = hitId, assignmentId=assignmentId, workerId=workerId,EGParameters=EGParameters);
        else:
          print "Error, user appears in database more than once (serious problem)"
          raise ExperimentError( 'user_appears_in_database_more_than_once' )
      elif(request.form['loginsignin']=="returning"): # user already exists in db
        if(EGParameters['withPassword']=='n'):
          return render_template('/eg/login.html',flag="APOLOGIES_NORETURN",loginValues=loginValues,EGParameters=EGParameters);
        else:
          query="select * from users where username="+GetSQLValueString(username, 'text')+" and password="+GetSQLValueString(password, 'text')
          cursor.execute(query);
          if(cursor.rowcount==0):
            return render_template('/eg/login.html',flag="AUTH_FAILED",loginValues=loginValues,EGParameters=EGParameters);
          elif(cursor.rowcount==1):
            row=cursor.fetchone()
            row['ipaddress']=ipaddress
            row['lastvisit']=datetime.now()
            row['sessionId']=random.randint(10000000, 99999999)
            user = User(row,'update')
            # Gameset running for this user ?
            # 23032015 : keyCodeMode check
            if EGParameters['keyCodeMode']=='y':
              query_rs_keyCode="select count(*) as count from keycode_gameset_user, gamesets"+\
                               " where userid="+str(user.id)+" and keycode_gameset_user.gamesetid=gamesets.id"+\
                               " and gamesets.status<>3 and keycode_gameset_user.status='IN_USE'"
              cursor.execute(query_rs_keyCode)
              row_rs_keyCode=cursor.fetchone()
              gameset_running_for_user=False
              if(row_rs_keyCode['count']>1):
                raise ExperimentError( 'user_has_more_than_one_gameset_not_terminated_and_keycode_in_use' )
              elif(row_rs_keyCode['count']==1):
                gameset_running_for_user=True
              if(userId_of_givenKeyCodeBegin==-1):
                if(gameset_running_for_user): # gameset running (status=<>3) for the user
                  return render_template('/eg/login.html',flag="KEYCODE_GIVEN_WHILE_ANOTHER_IN_USE_FOR_A_NON_TERMINATED_GAMESET",loginValues=loginValues,EGParameters=EGParameters);
                else:
                  #print "update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text")
                  cursor.execute("update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE', usagetime='"+str(datetime.now())+"' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text"))
                  connection.commit()
              else:
                if(userId_of_givenKeyCodeBegin==user.id):
                  print 'returning user in its gameset : ',gameSetId_of_givenCodeKeyCodeBegin
                else:
                  return render_template('/eg/login.html',flag="KEYCODE_ALREADY_USED",loginValues=loginValues,EGParameters=EGParameters);
            return render_template('/eg/consent.html',sessionId=user.sessionId, hitId = "0", assignmentId="0", workerId=str(user.id),EGParameters=EGParameters);
          else:
            print "Error, user appears in database more than once (serious problem)"
            raise ExperimentError( 'user_appears_in_database_more_than_once' )
      # end elif(request.form['loginsignin']=="returning")
      # added for robot
      elif(request.form['loginsignin']=="robot"):
        # 6
        #sqla matchesUser = User.query.filter(User.username == username).filter(User.password == password).all();
        query="select * from users where username="+GetSQLValueString(username, 'text')+" and password="+GetSQLValueString(password, 'text')
        cursor.execute(query);
        row=cursor.fetchone()
        row['ipaddress']=ipaddress
        row['ipaddress']='n'
        row['lastvisit']=datetime.now()
        row['sessionId']=random.randint(10000000, 99999999)
        user = User(row,'update')
        workerId = str(user.id);
        assignmentId = "0";
        hitId = "0";
        if EGParameters['skipConsentInstruct']=='y' :
          user.status=User.INSTRUCTED
          user.update()
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
      cursor.execute(query)
      duplicate_primarykey=False
    except:
      duplicate_primarykey=True
  return json.dumps({'keyCodeBegin':robotkeycode,'username':username,'loginsignin':'robot','pwd':'','pwd2':'','skipConsentInstruct':EGParameters['skipConsentInstruct']});
# end added for robot 

def NewUser(username,password,ipaddress):#
  user = User({'username':username,'password':password,'ipaddress':ipaddress,'lastvisit':datetime.now(),'sessionId':str(random.randint(10000000, 99999999))},'insert');
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
    query="select * from users where id="+GetSQLValueString(workerId, 'int')
    cursor.execute(query);
    #sqla  if(len(matches)==0):
    if(cursor.rowcount==0):
        to_return = render_template('/eg/login.html',flag="SESSION_EXPIRED",loginValues=loginValues,EGParameters=EGParameters);                       
        return [hitId,assignmentId,workerId,None,to_return]
    elif(cursor.rowcount>1):
        print "User in db more than once, serious trouble"
        raise  ExperimentError('user_in_db_more_than_once')
    row=cursor.fetchone()
    user = User(row,'select')
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
        if EGParameters['skipQuestionnaire']=='y':
          user.status = User.ASSESSED
        user.update()
    
    res = redirect(user,hitId,assignmentId,workerId,user.sessionId)
    return res

def findParticipant(hitId,assignmentId,workerId,addIfNotFound):
    query="select * from participants where hitId="+GetSQLValueString(hitId, 'text')+" and assignmentId="+GetSQLValueString(assignmentId, 'text')+" and workerId="+GetSQLValueString(workerId, 'text')
    cursor.execute(query);
    numrecs = cursor.rowcount
    if numrecs == 0:
        #print 'Participant not in database yet'
        if(addIfNotFound):
            # Choose condition and counterbalance, subj_cond, subj_counter = get_random_condcount()
            if not request.remote_addr:
                myip = "UKNOWNIP"
            else:
                myip = request.remote_addr
            # set condition here and insert into database
            part = Participant({'hitId':hitId, 'ipaddress':myip, 'assignmentId':assignmentId, 'workerId':workerId,'status':Participant.INSTRUCTED},'insert')#,'cond':0, 'counterbalance':0
            return part
        else:
            return False
    elif numrecs == 1:
        part = Participant(cursor.fetchone(),'select')
        return part
    else:
        print "Error, hit/assignment appears in database more than once (serious problem)"
        raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )

def findUser(workerId):
    query="select * from users where id="+GetSQLValueString(workerId, 'int')
    cursor.execute(query);
    numrecs = cursor.rowcount
    if numrecs == 0:
        #print 'User not in database yet'
        return False
    elif numrecs == 1:
        user=User(cursor.fetchone(),'select')
        return user
    else:
        print "Error, hit/assignment appears in database more than once (serious problem)"
        raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )

def redirect(user,hitId,assignmentId,workerId,sessionId):
  # skipConsentInstruct for test : go directly to waitingroom to avoid firsts pages
  if not EGParameters['EGRunning']:
    return render_template('/eg/login.html',flag="LOGIN_NOT_OPEN",loginValues={'keyCodeBegin':'','username':'','loginsignin':'','pwd':'','pwd2':''}, EGParameters=EGParameters);
  
  if EGParameters['skipConsentInstruct']=='y' :
    user.status=User.INSTRUCTED
    user.update()
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
      user.update()
    return redirect(user,hitId,assignmentId,workerId,user.sessionId)


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
    query="select * from gamesets,participants"+\
          " where gamesets.id=participants.assignmentId and workerId="+GetSQLValueString(str(user.id), 'text')+" and gamesets.status<>"+str(GameSet.TERMINATED)
    cursor.execute(query)
    number_of_currentGamesets = cursor.rowcount
    if number_of_currentGamesets!=0:
      gameset=GameSet(cursor.fetchone(),'select')

    #sqla if len(currentGamesets)== 0:# user not in a current gameset
    if number_of_currentGamesets== 0:# user not in a current gameset
        # assign a gameset to the participant        
        query="select gamesets.*"+\
              " from gamesets,participants"+\
              " where gamesets.id=participants.assignmentId and gamesets.status!="+GetSQLValueString(GameSet.TERMINATED,'int')+\
              " group by gamesets.id"+\
              " having count(gamesets.id)<gamesets.numExpectedParticipants"+\
              " order by count(gamesets.id) desc"
        cursor.execute(query)
        number_of_vacantGameSets=cursor.rowcount
        if number_of_vacantGameSets!=0:
          gameset=GameSet(cursor.fetchone(),'select')
        # 12092016 added by PG
        if EGParameters['addRobotsMode']=='y' and not request.args.has_key('robot') : # in addRobotsMode, a user (not robot) always create a new gameset
          number_of_vacantGameSets=0
        if(number_of_vacantGameSets==0 and not request.args.has_key('robot')):# a robot may not create a gameset
            query="select count(*) as num_free_images from image where image.status="+str(Image.FREE)+" and image.pic_type="+GetSQLValueString(EGParameters['imageType'], 'text')
            cursor.execute(query)
            row = cursor.fetchone()
            num_free_images=row['num_free_images']
            if(num_free_images < EGParameters['numGames']*EGParameters['columnNumber'] and not EGParameters['useExistingGames']=='y' and not EGParameters['redundantMode']=='y'):
              raise ExperimentError('not_enough_images_for_the_gameset')
            gameset = GameSet({'numExpectedParticipants':EGParameters['numExpectedParticipants'],'numGames':EGParameters['numGames'],
                                'starttime':datetime.now(),'playmode':EGParameters['playMode'],'job_id':EGParameters['job_id']},'insert')
            #gameset.insert()
            
            #creation of the part : link between user and gameset
            addIfNotFound = True # added in consent only
            part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)
            gamesetsRunningList[str(gameset.id)]=dict()
            gamesetsRunningList[str(gameset.id)]['users']=dict()
            gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']=nowDate
            #print "gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']="+str(nowDate.strftime('%Y%m%d-%H%M%S-%f'))
            # 19082016
            gamesetsRunningList[str(gameset.id)]['users_and_robots']=dict() #no_sqla
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
                game = Game({'num':numgame,'numExpectedParticipants':gameset.numExpectedParticipants,'numRounds':EGParameters['numRounds'],'gamesetid':gameset.id},'insert');
                game_images=game.addImages(EGParameters)
                game_pic_list=[]
                for numimage in range(0,EGParameters['columnNumber']):
                  game_pic_list.append(game_images[numimage].pic_name)
                gameset_pic_list.append(game_pic_list)
            gameset.pic_name='gameset_'+str(gameset.id)+'_'+str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
            gameset.update()
            create_gameset_picture(EGParameters,gameset_pic_list,gameset.pic_name,int(EGParameters['imgsize']),int(EGParameters['imgsize']))
            hidId = str(gameset.id);
            assignmentId = str(gameset.id);            
            part.hitId = hidId;
            part.assignmentId = assignmentId;
            part.update() #no sqla
        else:# gameset exists : user (or robot) added as a participant in the gameset
            #retrieval of the part : link between user and gameset
            addIfNotFound = True # added in consent only
            part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)            
            if(not part):
                raise ExperimentError('participant_not_found_gameset_exists_waiting_room')
            query="select * from games where num="+GetSQLValueString(1,'int')+" and gamesetid="+GetSQLValueString(gameset.id, 'int')
            cursor.execute(query);
            game=Game(cursor.fetchone(),'select')
        # 23032015 : check for keyCodeMode
        if EGParameters['keyCodeMode']=='y':
          query="select count(*) as count from keycode_gameset_user where userid="+GetSQLValueString(user.id,'int')+" and  status='IN_USE' and gamesetid=-1"
          cursor.execute(query);
          row=cursor.fetchone()
          if(row['count']==1):
            query="update keycode_gameset_user set gamesetid="+GetSQLValueString(gameset.id, 'int')+\
                  " where userid="+GetSQLValueString(user.id,'int')+" and  status='IN_USE' and gamesetid=-1"
            cursor.execute(query);
            connection.commit()
          else:
            raise ExperimentError('user_has_0_or_more_than_1_keycode_in_use')
    elif (number_of_currentGamesets== 1): 
        try:
          query="select games.* from games where status="+GetSQLValueString(Game.STARTED,'int')+" and gamesetid="+GetSQLValueString(gameset.id, 'int')
          cursor.execute(query);
          game=Game(cursor.fetchone(),'select')
        except:
          try:
            query="select * from games where num="+GetSQLValueString(1,'int')+" and gamesetid="+GetSQLValueString(gameset.id, 'int')
            cursor.execute(query);
            game=Game(cursor.fetchone(),'select')
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
                
    numParticipants=len(gamesetsRunningList[str(gameset.id)]['users_and_robots'])
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
    if not workerId in gamesetsRunningList[str(gameset.id)]['users_and_robots']:
      gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]=dict()
      gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]['decisionval']=0
      gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]['numpart']=numParticipants
      gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]['isChoiceMade']=False
    
    # start the gameset if forceStartAfterWait is set and elapsed time in the waiting room for the first participant is greater than forceStartAfterWaitDelay
    # and forceStartAfterWaitNumParticipants = number of participants in the waiting room
    leftDelayToBeginGameSet=0
    missingParticipant=gameset.numExpectedParticipants - numParticipants
    if EGParameters['forceStartAfterWait']=='y':
      missingParticipant=max(0,EGParameters['forceStartAfterWaitNumParticipants'] - numParticipants)
      leftDelayToBeginGameSet=EGParameters['forceStartAfterWaitDelay']*60-(nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()
      if missingParticipant==0 and leftDelayToBeginGameSet<=0:
        # if forceStartAfterWaitDelay has expired
        gameset.numExpectedParticipants=numParticipants
        gameset.update()
        cursor.execute("update games set numExpectedParticipants="+GetSQLValueString(numParticipants,'int')+" where gamesetid="+str(gameset.id))
        connection.commit()
    
    stop_the_gameset_no_other_participant_timeleft=EGParameters['stop_the_gameset_no_other_participant_delay']*60-(nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()
    
    if(missingParticipant>0 or (EGParameters['forceStartAfterWait']=='y' and leftDelayToBeginGameSet>0)):#not enough participants or too early
      if (request.args.has_key('getFlag')):
        # start robots process if not already started. Robots process are started one time, not more when gamesetsRunningList[assignmentId]['robots_process_state']=='wait'
        # A robot cannot start robots process !
        #if not request.args.has_key('robot') and EGParameters['addRobotsMode']=='y' and EGParameters['useExistingGames']=='y' and gamesetsRunningList[assignmentId]['robots_process_state']=='wait':
        if not request.args.has_key('robot') and EGParameters['addRobotsMode']=='y' and gamesetsRunningList[assignmentId]['robots_process_state']=='wait':
          for i in range(0,gameset.numExpectedParticipants - numParticipants):
            os.spawnl(os.P_NOWAIT, r'/usr/local/php/bin/php','php', str(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+'/robot_eg.php '))+str(EGParameters['httpPort']))
            #os.spawnl(os.P_NOWAIT, phpPath,'php', 'robot_eg.php ')
          gamesetsRunningList[assignmentId]['robots_process_state']='started'
        # end start robots process
        if(EGParameters['stop_the_gameset_no_other_participant']=='y' and numParticipants==1 and (nowDate-gamesetsRunningList[str(gameset.id)]['startWaitingRoomTime']).total_seconds()>EGParameters['stop_the_gameset_no_other_participant_delay']*60):
          gamesetsRunningList[str(gameset.id)]['stop_the_gameset_no_other_participant_time']=nowDate
          gameset.status = GameSet.TERMINATED
          gameset.update()
          return json.dumps({'status':'stop_the_gameset_no_other_participant'})
        else:
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
    elif(missingParticipant==0):#enough participants
        listOfChoices=[]
        for i in range(0,3):
          initlist=[]
          for j in range(0,gameset.numExpectedParticipants):
            initlist.append(0)
          listOfChoices.append(initlist)
        gamesetsRunningList[str(gameset.id)]['listOfChoices']=listOfChoices
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
    # check first to see if this hitId or assignmentId exists.  if so check to see if inExp is set
    if(part==None):#try to set part
      [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
      sessionId=user.sessionId
      if to_return!=None:#print "returning to login"
        return to_return
      addIfNotFound = False # added in consent only
      part = findParticipant(str(hitId),str(hitId),str(user.id),addIfNotFound)
    else : #"Participant given as parameter"
      hitId, assignmentId, workerId = part.hitId, part.assignmentId, part.workerId;
      query="select sessionId from users where id="+GetSQLValueString(workerId, 'int')
      cursor.execute(query);
      row=cursor.fetchone()
      sessionId=row['sessionId']
    
    if not assignmentId in gamesetsRunningList:
      if not workerId in gamesetsRunningList[assignmentId]['users_and_robots']:
        return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=sessionId,gameset_pic_name="",EGParameters=EGParameters)
    query="select * from gamesets where id="+GetSQLValueString(assignmentId, 'int')
    cursor.execute(query);
    gameset=GameSet(cursor.fetchone(),'select')
    try:
      query="select games.* from games where status="+GetSQLValueString(Game.STARTED,'int')+" and gamesetid="+GetSQLValueString(gameset.id, 'int')
      cursor.execute(query);
      curgame=Game(cursor.fetchone(),'select')
    except:
      try:
        query="select * from games where gamesetid="+GetSQLValueString(gameset.id, 'int')+" and num="+GetSQLValueString(1,'int')
        cursor.execute(query);
        curgame=Game(cursor.fetchone(),'select')
      except:
        raise ExperimentError('game_not_found_for_gameset_not_terminated')
    
    
    if not curgame.status==Game.STARTED:
      curgame.status=Game.STARTED
      curgame.update()
    # Preventing trouble    
    numParticipants = len(gamesetsRunningList[str(gameset.id)]['users_and_robots'])
    if(gameset.numExpectedParticipants > numParticipants):
      return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, missingChoices=str(gameset.numExpectedParticipants - numParticipants),sessionId=user.sessionId,gameset_pic_name="",EGParameters=EGParameters)
    elif(gameset.numExpectedParticipants < numParticipants):
      raise ExperimentError( 'too_many_participants' )

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

    curgameImagesTuple=curgame.getImagesTuple()
    color=[]
    for i in range(0,3):
      color.append(curgameImagesTuple[i].color)
    expconsensusAttributes = {'workerId': part.workerId,
                              'assignmentId': part.assignmentId,
                              'hitId' : part.hitId, 
                              'sessionId' : sessionId,
                              #'cond' : part.cond, 
                              #'counter' : part.counterbalance, 
                              'question' : question,                                                                            
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
    #POST : form sent by user
    if(len(request.form)>0 and not request.form.has_key('No decision')):
      query="select * from rounds where gameid="+GetSQLValueString(curgame.id,'int')+ " and  num="+GetSQLValueString(curgame.getCurRoundNum(),'int')
      cursor.execute(query);
      curround=Round(cursor.fetchone(),'select')
      # Add the participant new choice and decisions
      expconsensusAttributes['round']=curround.num
      if((not gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]['isChoiceMade'] or EGParameters['playMode']=='continuous')
          and curround.num == int(request.form['roundNum']) and curround.status!=Round.TERMINATED):# 21112016 added curround.status!=Round.TERMINATED
        tab_decision=dict()
        for i in range(0,3):
          if request.form['auto'+str(i)]==1:
            auto=Decision.AUTO
          else :
            auto=Decision.USER_MADE;
          tab_decision[i]={'auto':auto,'value':request.form['decision'+str(i)]}
        registerChoice(assignmentId,workerId,curround,curgame.num,curgameImagesTuple,tab_decision)
        
        if (curround.type==Round.LONE or EGParameters['playMode']=='discrete') :
          expconsensusAttributes['status'] = "CHOICE_MADE"
        else :
          expconsensusAttributes['status'] = "CHOICE_TO_BE_MADE"
        # 21112016 corrected 
        # if(EGParameters['imageType']=='fractal') :
          # gamesetsRunningList[str(gameset.id)]['listOfChoices'][0][gamesetsRunningList[str(gameset.id)]['users_and_robots'][part.workerId]['decisionval']]=float(tab_decision[0]['value']) 
        # else :
          # gamesetsRunningList[str(gameset.id)]['listOfChoices'][0][gamesetsRunningList[str(gameset.id)]['users_and_robots'][part.workerId]['decisionval']]=int(tab_decision[0]['value'])  
        numpart=gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]['numpart']
        if(EGParameters['imageType']=='fractal') :
          gamesetsRunningList[str(gameset.id)]['users_and_robots'][part.workerId]['decisionval']=float(tab_decision[0]['value'])
          gamesetsRunningList[str(gameset.id)]['listOfChoices'][0][numpart]=float(tab_decision[0]['value']) 
        else :
          gamesetsRunningList[str(gameset.id)]['users_and_robots'][part.workerId]['decisionval']=int(tab_decision[0]['value'])
          gamesetsRunningList[str(gameset.id)]['listOfChoices'][0][numpart]=int(tab_decision[0]['value'])  
        #  21112016 corrected end
        missingChoices=missingChoicesRound(gameset.id)
        expconsensusAttributes['missingChoices'] = str(missingChoices);
        if(missingChoices==0 and (curround.type==Round.LONE or EGParameters['playMode']=='discrete')):
          [htmlStatus,curround] = terminateRound(curround,curgame,gameset)
          if(htmlStatus!=""):
            expconsensusAttributes['status'] = htmlStatus
        # Redirect to an intermediate page to avoid double posting
        if (curround.type==Round.LONE or EGParameters['playMode']=='discrete') :
          # 20161211 return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=sessionId,EGParameters=EGParameters)
          return ('', 204)# 20161211 
    curRoundNum=curgame.getCurRoundNum()
    if(curRoundNum==0):# Setting the first round
      curround=startNewRound(curgame,curRoundNum)
    else:
      query="select * from rounds where gameid="+GetSQLValueString(curgame.id,'int')+ " and  num="+GetSQLValueString(curRoundNum,'int')
      cursor.execute(query);
      curround=Round(cursor.fetchone(),'select')
    # curgame and curround are ready
    expconsensusAttributes['round']=curround.num
    expconsensusAttributes['game']=curgame.num
    if(curround.num>1):# SOCIAL rounds
      listprevround=gamesetsRunningList[str(gameset.id)]['listOfChoices']
      numpart=gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]['numpart']
      listprevchoice = [gamesetsRunningList[str(gameset.id)]['listOfChoices'][0][numpart],0,0]
      expconsensusAttributes['prevRoundHTML']=json.dumps(listprevround);
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
    # curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curRoundNum==Round.num).one()
    
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
      if not gamesetsRunningList[str(gameset.id)]['users_and_robots'][workerId]['isChoiceMade']:
        boolIntermediatePage = True
      tab_decision=dict()
      for i in range(0,3):
        tab_decision[i]={'auto':Decision.AUTO,'value':0}
      for a_workerId in gamesetsRunningList[str(gameset.id)]['users_and_robots']:
        if not gamesetsRunningList[str(gameset.id)]['users_and_robots'][a_workerId]['isChoiceMade']:
          registerChoice(str(gameset.id),a_workerId,curround,curgame.num,curgameImagesTuple,tab_decision)
      expconsensusAttributes['status'] = "CHOICE_MADE" # default : may be changed if(missingChoices==0) bellow 
      missingChoices=missingChoicesRound(gameset.id)
      expconsensusAttributes['missingChoices'] = str(missingChoices);
      if(missingChoices==0 and curround.status!=Round.TERMINATED):# 21112016 added curround.status!=Round.TERMINATED
        #print 'if remaining time out of limit, if missingChoices==0'
        [htmlStatus,curround] = terminateRound(curround,curgame,gameset)
        if(htmlStatus!=""):
          expconsensusAttributes['status'] = htmlStatus
      # Redirect to an intermediate page to avoid double posting
      if(boolIntermediatePage):
        # 20161211 return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=sessionId,EGParameters=EGParameters)
        return ('', 204)# 20161211 
    try:
      query="select games.* from games where status="+GetSQLValueString(Game.STARTED,'int')+" and gamesetid="+GetSQLValueString(gameset.id, 'int')
      cursor.execute(query);
      curgame=Game(cursor.fetchone(),'select')
    except:
      try:
        query="select * from games where gamesetid="+GetSQLValueString(gameset.id, 'int')+" and num="+GetSQLValueString(1,'int')
        cursor.execute(query);
        curgame=Game(cursor.fetchone(),'select')
      except:
        raise ExperimentError('game_not_found_for_gameset_not_terminated')

    query="select * from rounds where gameid="+GetSQLValueString(curgame.id,'int')+ " and  num="+GetSQLValueString(curgame.getCurRoundNum(),'int')
    cursor.execute(query);
    curround=Round(cursor.fetchone(),'select')
    
    if gamesetsRunningList[str(gameset.id)]['users_and_robots'][part.workerId]['isChoiceMade']:
      # PG : expconsensusAttributes['status'] = "CHOICE_MADE"
      if(curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout):
        expconsensusAttributes['status'] = "CHOICE_MADE"
      else: # continuous social round
        expconsensusAttributes['status'] = "CHOICE_TO_BE_MADE"
      # continuous version : distinct participants number in choices for this round
      missingChoices=missingChoicesRound(gameset.id)
      expconsensusAttributes['missingChoices'] = str(missingChoices)
      # before continuous version : if(missingChoices==0 and curround.num == curgame.numRounds):
      if(missingChoices==0 and curround.num == curgame.numRounds and (curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout)):
        if(curgame.num==gameset.numGames):
          expconsensusAttributes['status'] = "GAMESET_OVER"
          gameset.status = GameSet.TERMINATED;
          gameset.update()
        else:
          expconsensusAttributes['status'] = "GAME_OVER"
          curgame.status = Game.TERMINATED;
          curgame.update()
          #new game
          query="update games set status="+GetSQLValueString(Game.STARTED,'int')+" where num="+GetSQLValueString(curgame.num+1,'int')+" and gamesetid="+GetSQLValueString(gameset.id,'int')
          cursor.execute()
          connection.commit()
    else:
      expconsensusAttributes['status'] = "CHOICE_TO_BE_MADE"
    
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
        expconsensusAttributes['sessionId']=sessionId
        return render_expconsensus(part,**expconsensusAttributes)
      else :
        return ('', 204)
  
def render_expconsensus(part,**expconsensusAttributes):
    if(part.status < Participant.STARTED):
        part.status=Participant.STARTED
        part.update()
        if expconsensusAttributes['status'] == "CHOICE_TO_BE_MADE":
          expconsensusAttributes['sound']=1
        else :
          expconsensusAttributes['sound']=0
    else:
        expconsensusAttributes['sound']=0
    return render_template('/eg/expconsensus.html',EGParameters=EGParameters, **expconsensusAttributes)

def missingChoicesRound(gamesetid):
  missingChoices=0
  for a_workerId in gamesetsRunningList[str(gamesetid)]['users_and_robots']:
    if not gamesetsRunningList[str(gamesetid)]['users_and_robots'][a_workerId]['isChoiceMade']:
      missingChoices=missingChoices+1
  return missingChoices
    
def terminateRound(curround,curgame,gameset) :
  # 20150502 : redundant images in discrete mode : adjust decisions of robots with the user decisons in the previous game with original image
  if EGParameters['redundantMode']=='y' and curround.status!=Round.TERMINATED:
    for decisionnum in range(0,EGParameters['columnNumber']):
      if str(curgame.num)+'#'+str(curround.num)+'#'+str(decisionnum) in gamesetsRunningList[str(gameset.id)]['tab_of_redundant_images']:
        userworkerId=gamesetsRunningList[str(gameset.id)]['users'].keys()[0];
        query= "select decisions.value,decisions.status from decisions,choices,rounds,games"+\
                  " where decisions.choiceid=choices.id and choices.roundid=rounds.id and rounds.gameid=games.id and choices.workerId="+GetSQLValueString(userworkerId,'int')+\
                  " and games.num="+GetSQLValueString(curgame.num,'int')+" and rounds.num=1 and decisions.num="+GetSQLValueString(decisionnum,'int')+\
                  " and games.gamesetid="+GetSQLValueString(gameset.id,'int')
        cursor.execute(query)
        row=cursor.fetchone()
        if row['status']==Decision.USER_MADE :
          currentdecisionval=row['value']
          # user's decision in game, round 1, decision num for the previous occurence of this redundant image
          tab=split(gamesetsRunningList[str(gameset.id)]['tab_of_redundant_images'][str(curgame.num)+'#'+str(curround.num)+'#'+str(decisionnum)],'#')
          query= "select decisions.value,decisions.status from decisions,choices,rounds,games"+\
                 " where decisions.choiceid=choices.id and choices.roundid=rounds.id and rounds.gameid=games.id and choices.workerId="+GetSQLValueString(userworkerId,'int')+\
                 " and games.num="+GetSQLValueString(tab[0],'int')+" and rounds.num=1 and decisions.num="+GetSQLValueString(tab[2],'int')+" and games.gamesetid="+GetSQLValueString(gameset.id,'int')
          cursor.execute(query)
          row=cursor.fetchone()
          if row['status']==Decision.USER_MADE :
            delta=currentdecisionval-row['value']
            cursor.execute("update decisions,choices,rounds,games set decisions.value=least("+EGParameters['maxDecisionValue']+",greatest("+EGParameters['minDecisionValue']+",decisions.value+"+str(delta)+"))"\
                            " where decisions.choiceid=choices.id and choices.roundid=rounds.id and rounds.gameid=games.id and choices.workerId<>"+str(userworkerId)+\
                            " and games.num="+str(curgame.num)+" and rounds.num="+str(curround.num)+" and decisions.num="+str(decisionnum)+" and games.gamesetid="+str(gameset.id))
            connection.commit()
  curround.status=Round.TERMINATED;
  curround.endTime = datetime.now()
  curround.update()
  htmlStatus = "";
  if(curround.num==curgame.numRounds):
    if(curgame.num==gameset.numGames):
      htmlStatus = "GAMESET_OVER"
      gameset.status = GameSet.TERMINATED;
      gameset.update()
    else:
      htmlStatus = "GAME_OVER"
      curgame.status = Game.TERMINATED;
      curgame.update()
      #new game
      query="select games.* from games where num="+GetSQLValueString(curgame.num+1,'int')+" and gamesetid="+GetSQLValueString(gameset.id, 'int')
      cursor.execute(query);
      newgame=Game(cursor.fetchone(),'select')
      newgame.status=Game.STARTED
      newgame.update()
      #new round
      curRoundNum=0
      curround = startNewRound(newgame,curRoundNum)
    
      listOfChoices=[]
      for i in range(0,3):
        initlist=[]
        for j in range(0,gameset.numExpectedParticipants):
          initlist.append(0)
        listOfChoices.append(initlist)
      gamesetsRunningList[str(gameset.id)]['listOfChoices']=listOfChoices
  else:
    # Starting a new round
    curround = startNewRound(curgame,curround.num)
  
  return [htmlStatus,curround]

def startNewRound(curgame,curRoundNum):
# Starting a new round in the game curgame (requires curgame not to be over)
    num = curRoundNum+1
    #if((curgame.num==1 and num<=1) or (curgame.num>1 and num==1)):
    if(num==1):
        type = Round.LONE;
        if EGParameters['playMode']=='discrete':
          maxreward = EGParameters['loneMaxReward'];
        else:
          maxreward = 1
    else:
        type = Round.SOCIAL;
        if EGParameters['playMode']=='discrete':
          maxreward = EGParameters['socialMaxReward'];
        else:
          maxreward = 1        
    status = Round.STARTED
    startTime = datetime.now()
    round = Round({'num':num,'status':status,'type':type,'startTime':startTime,'maxreward':maxreward,'gameid':curgame.id},'insert')
    for a_workerId in gamesetsRunningList[str(curgame.gamesetid)]['users_and_robots']:
      gamesetsRunningList[str(curgame.gamesetid)]['users_and_robots'][a_workerId]['isChoiceMade']=False
    return round
   
def registerChoice(assignmentId,workerId,round,gamenum,gameImagesTuple,tab_decision):
    timestamp=datetime.now()
    total_errorsize=0
    for i in range(0,3):
      choice = Choice({'roundid':round.id,'assignmentId':assignmentId,'workerId':workerId},'insert')
      errorsize = abs(float(tab_decision[i]['value']) - gameImagesTuple[i].percent)/EGParameters['ratioForErrorSize'];
      reward = computeReward(errorsize,round.maxreward)
      decision=Decision({'status':tab_decision[i]['auto'],'num':i,'value':tab_decision[i]['value'],'timestamp':timestamp,'reward':reward,'choiceid':choice.id,'imageid':gameImagesTuple[i].id},'insert') 
      total_errorsize=total_errorsize+errorsize
    # store user errorsizes. After 3 games, the average is computed with 3 rounds/game
    if workerId in gamesetsRunningList[assignmentId]['users']:# not a robot
      if round.num==1 and gamenum%3==1 :
        gamesetsRunningList[assignmentId]['users'][workerId]['errorsize']=int(total_errorsize)
      elif round.num==3 and gamenum%3==0 :
        gamesetsRunningList[assignmentId]['users'][workerId]['errorsize']=int(gamesetsRunningList[assignmentId]['users'][workerId]['errorsize']/27)*EGParameters['ratioForErrorSize'];
      else :
        gamesetsRunningList[assignmentId]['users'][workerId]['errorsize']=int(total_errorsize+gamesetsRunningList[assignmentId]['users'][workerId]['errorsize'])
    gamesetsRunningList[assignmentId]['users_and_robots'][workerId]['isChoiceMade']=True
        
def computeReward(errorsize,maxreward):
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

@app.route('/eg/questionnaire_first', methods=['POST', 'GET'])
def questionnaire_first():
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    
    query="select * from questionnaires where userid="+GetSQLValueString(user.id, 'int')
    cursor.execute(query)
    if request.method == 'GET':
      if cursor.rowcount==1:
        questionnaire=Questionnaire(cursor.fetchone(),'select')
        questionnaire.enterQtime=datetime.now()
        questionnaire.update()
      else:
        questionnaire = Questionnaire({'userid':user.id,'enterQtime':datetime.now()},'insert');
      
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
      if not request.args.has_key('robot'):
        questionnaire=Questionnaire(cursor.fetchone(),'select')
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
        questionnaire.update()
      user.status = User.ASSESSED
      user.update()        
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
      addIfNotFound=False
      part = findParticipant(hitId,assignmentId,workerId,addIfNotFound)
    except:
      raise ExperimentError('improper_inputs')
    
    # init tab_userdecision

    if(workerId in gamesetsRunningList[part.assignmentId]['users']): # not a robot
      gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision']=dict()
    
      if EGParameters['playMode']=='discrete':
        maxpoints=EGParameters['numGames']*(EGParameters['loneMaxReward']+(EGParameters['numRounds']-1)*EGParameters['socialMaxReward'])
        query="select games.num as gamenum, decisions.num, decisions.value as decisionval, decisions.reward as reward"+\
                   " from decisions, choices, rounds, games"+\
                   " where decisions.choiceid=choices.id and choices.roundid=rounds.id"+\
                   " and rounds.gameid=games.id"+\
                   " and choices.assignmentid='"+part.assignmentId+"' and choices.workerid='"+part.workerId+"'"+\
                   " order by games.num asc, decisions.num asc"
        cursor.execute()
        rows=cursor.fetchall()
        prev_gamenum=-1
        for row in rows:
          gamenum=row['gamenum']
          if prev_gamenum!=row['gamenum']:
            gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][gamenum]=dict()
            prev_gamenum=gamenum
          decisionval=row['decisionval']
          if(EGParameters['imageType'] == 'peanut'):
            decisionval=int(decision.value)
          # SOCIAL decisions erase LONE decisions
          gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][gamenum][decisionnum+1]=decisionval
          totalreward = totalreward+row['reward']
        #if totalreward>EGParameters['bonusFloor']*maxpoints :
          #bonus=1
      else : #continuous
        query="select games.num as gamenum,games.id as gameid,"+\
                   "rounds.num as roundnum,rounds.type as roundtype,rounds.startTime as roundstarttime,rounds.endTime as roundendtime,"+\
                   " decisions.timestamp as decisiontime, decisions.status, decisions.value as decisionval, decisions.reward"+\
                   " from decisions, choices, rounds, games"+\
                   " where decisions.choiceid=choices.id and choices.roundid=rounds.id"+\
                   " and rounds.gameid=games.id"+\
                   " and choices.assignmentid='"+part.assignmentId+"' and choices.workerid='"+part.workerId+"'"+\
                   " and decisions.num=0"+\
                   " order by decisions.timestamp asc"
        cursor.execute(query)
        rows=cursor.fetchall()
        prev_roundnum=-1
        prev_roundstarttime=""
        prev_decisiontime=""
        prev_reward=0
        prev_roundtype=Round.LONE
        duration=0
        indexrow=0
        htmltable=htmltable+'<table border="1"><tr><td nowrap>game</td><td nowrap>round</td><td nowrap>type</td><td nowrap>roundstart</td><td nowrap>roundend</td><td nowrap>prev decision</td><td nowrap>decision</td><td nowrap>duration</td><td nowrap>prev_decisionval</td><td nowrap>prev_reward</td><td nowrap>prev_reward*duration</td><td nowrap align="center">formule</td><td nowrap align="center">condition</td></tr>'
        for row in rows :
          htmltable=htmltable+'<tr>'
          indexrow=indexrow+1
          gamenum=row['gamenum']
          roundnum=row['roundnum']
          roundtype=row['roundtype']
          roundstarttime=row['roundstarttime']
          roundendtime=row['roundendtime']
          decisiontime=row['decisiontime']
          decisionval=row['decisionval']
          if(EGParameters['imageType'] == 'peanut'):
            decisionval=int(row['decisionval'])
          reward=row['reward']
          formule=''
          if roundtype==Round.LONE :# compute previous duration between decision and end of round 
            if gamenum==1 :
              htmltable=htmltable+'<td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>LONE</td><td nowrap>'+roundstarttime.strftime("%H:%M:%S")+\
                                  '</td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap>'+\
                                  '</td><td nowrap>'+decisiontime.strftime("%H:%M:%S")+'</td><td nowrap></td><td nowrap></td><td nowrap>'+\
                                  '</td><td nowrap></td><td nowrap></td><td nowrap>LONE et gamenum=1</td>'
            else :
              duration=max(0,(prev_roundstarttime-prev_decisiontime).total_seconds()+EGParameters['socialRoundDuration']+EGParameters['decision_out_of_limit_time'])
              formule='(prev_roundstarttime+socialRoundDuration+decision_out_of_limit_time)-prev_decisiontime'
              htmltable=htmltable+'<td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>LONE</td><td nowrap>'+roundstarttime.strftime("%H:%M:%S")+\
                                  '</td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap class="red16"><b>'+prev_decisiontime.strftime("%H:%M:%S")+\
                                  '</b></td><td nowrap>'+decisiontime.strftime("%H:%M:%S")+'</td><td nowrap>'+str(duration)+'</td><td nowrap>'+str(prev_decisionval)+'</td><td nowrap>'+\
                                  str(prev_reward)+'</td><td nowrap>'+str(prev_reward*duration)+'</td><td nowrap>'+formule+'</td><td nowrap>LONE et gamenum!=1</td>'
              # last decision in the SOCIAL round of the previous game
              gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][gamenum-1]=dict()
              gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision'][gamenum-1][1]=prev_decisionval
          else :
            if prev_roundnum!=roundnum :
              # duration from the begining of the SOCIAL round and the first decision in the SOCIAL round
              duration=max(0,(decisiontime-roundstarttime).total_seconds())
              formule='decisiontime-roundstarttime'
              htmltable=htmltable+'<td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>SOCIAL</td><td nowrap class="red16"><b>'+roundstarttime.strftime("%H:%M:%S")+'</b></td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap>'+prev_decisiontime.strftime("%H:%M:%S")+'</td><td nowrap class="red16"><b>'+decisiontime.strftime("%H:%M:%S")+'</b></td><td nowrap>'+str(duration)+'</td><td nowrap>'+str(prev_decisionval)+'</td><td nowrap>'+str(prev_reward)+'</td><td nowrap>'+str(prev_reward*duration)+'</td><td nowrap>'+formule+'</td><td nowrap>1ere decision et SOCIAL</td>'
            else:
              # duration between two decisions in the SOCIAL round          
              duration=max(0,(decisiontime-prev_decisiontime).total_seconds())            
              formule='decisiontime-previous_decisiontime '
              htmltable=htmltable+'<td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>SOCIAL</td><td nowrap>'+roundstarttime.strftime("%H:%M:%S")+'</td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap class="red16"><b>'+prev_decisiontime.strftime("%H:%M:%S")+'</b></td><td nowrap class="red16"><b>'+decisiontime.strftime("%H:%M:%S")+'</b></td><td nowrap>'+str(duration)+'</td><td nowrap>'+str(prev_decisionval)+'</td><td nowrap>'+str(prev_reward)+'</td><td nowrap>'+str(prev_reward*duration)+'</td><td nowrap>'+formule+'</td><td nowrap>decision SOCIAL</td>'
          totalreward=totalreward+prev_reward*duration
          prev_roundstarttime=roundstarttime
          prev_decisiontime=decisiontime
          prev_reward=reward
          prev_roundnum=roundnum
          prev_decisionval=decisionval
          htmltable=htmltable+'</tr>'
        # end of result set : last decision in the last social round 
        duration=max(0,(roundstarttime-decisiontime).total_seconds()+EGParameters['socialRoundDuration']+EGParameters['decision_out_of_limit_time'])
        formule='(roundstarttime+socialRoundDuration+decision_out_of_limit_time)-timedecision'
        totalreward=totalreward+reward*duration
        htmltable=htmltable+'<tr><td nowrap>game</td><td nowrap>round</td><td nowrap>type</td><td nowrap>roundstart</td><td nowrap>roundend</td><td nowrap>prev decision</td><td nowrap>decision</td><td nowrap>duration</td><td nowrap>decisionval</td><td nowrap>reward</td><td nowrap>reward*duration</td><td nowrap align="center">formule</td><td nowrap align="center">condition</td></tr>'
        htmltable=htmltable+'<tr><td nowrap>'+str(gamenum)+'</td><td nowrap>'+str(roundnum)+'</td><td nowrap>SOCIAL</td><td nowrap class="red16"><b>'+roundstarttime.strftime("%H:%M:%S")+'</b></td><td nowrap>'+roundendtime.strftime("%H:%M:%S")+'</td><td nowrap>'+prev_decisiontime.strftime("%H:%M:%S")+'</td><td nowrap class="red16"><b>'+decisiontime.strftime("%H:%M:%S")+'</b></td><td nowrap>'+str(duration)+'</td><td nowrap>'+str(decisionval)+'</td><td nowrap>'+str(reward)+'</td><td nowrap>'+str(reward*duration)+'</td><td nowrap>'+formule+'</td><td nowrap>derniere decision et SOCIAL</td></tr>'
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
    part.update()
    user.endhit = datetime.now()
    user.update()
    
    if EGParameters['keyCodeMode']=='y':
      query= "update keycode_gameset_user set status='USED',totalreward="+str(totalreward)+",bonus='"+bonus+"'"+\
                        " where userid="+workerId+" and gamesetid="+assignmentId
      
      cursor.execute(query)
      connection.commit()
      #print 'workerId=',workerId,'assignmentId',assignmentId
      try : # an "internal error" had occured one time during a gameset when selecting the keyCodeEnd, so we check for the exception
        query= "select keyCodeEnd from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
        cursor.execute(query)
        row=cursor.fetchone()
        keyCodeEnd=row['keyCodeEnd']
      except :
        keyCodeEnd='';
    email=user.email
    if email==None:
      email=''
    errorsize='0'
    if workerId in gamesetsRunningList[assignmentId]['users']: # not a robot
      errorsize=str(gamesetsRunningList[assignmentId]['users'][workerId]['errorsize'])
        
    # rank of the workerId in the whole classement
    query="SELECT workerId, round(avg( abs( decisions.value - image.percent ) / ( IF( pic_type = 'fractal', 1, 5 ) ) )) AS moy FROM choices, decisions, image WHERE choices.id = decisions.choiceid AND decisions.imageid = image.id GROUP BY workerId ORDER BY moy"
    cursor.execute(query)
    rows=cursor.fetchall()
    workernum=0
    posofworkerId=0
    for row in rows:
      workernum=workernum+1
      if(int(workerId)==int(row['workerId'])):
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
    if request.form.has_key('email'):
      user.email = request.form['email']
    if request.form.has_key('note'):
      user.note = request.form['note']
    user.update()
    
    addIfNotFound=False
    part = findParticipant(hitId,assignmentId,workerId,addIfNotFound)
    part.status = Participant.DEBRIEFED
    part.update()
    
    # 23032015
    if EGParameters['keyCodeMode']=='y':
      try : # an "internal error" had occured one time during a gameset when selecting the keyCodeEnd, so we check for the exception
        query= "select keyCodeEnd,bonus from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
        cursor.execute(query)
        row=cursor.fetchone()
        keyCodeEnd=row['keyCodeEnd']
        bonus=row['bonus']
      except :
        keyCodeEnd='';
        bonus=''
    # 26092016
    query="select games.num as numgame, image.id as imageid, percent as goodresponse "+\
             " from games, image"+\
             " where image.gameid=games.id and games.gamesetid="+part.assignmentId+\
             " order by games.num asc, image.id asc"
    cursor.execute(query)
    rows=cursor.fetchall()
    tab_goodresponse=dict()
    numgame=-1
    for row in rows:
      if row['numgame']!=numgame :
        numgame=int(row['numgame'])
        tab_goodresponse[row['numgame']]=dict()
        numcolumn=1
      if numcolumn<=EGParameters['columnNumber']:
        tab_goodresponse[numgame][numcolumn]=row['goodresponse']
        numcolumn=numcolumn+1
    
    tab_userdecision=dict()
    if workerId in gamesetsRunningList[assignmentId]['users']: # not a robot
      tab_userdecision=gamesetsRunningList[part.assignmentId]['users'][part.workerId]['tab_userdecision']
    
    tab_influencability=dict()
    if EGParameters['playMode']=='discrete':
       tab_influencability=influencability(assignmentId,workerId)
       
    # 15102016 list of last decision in each game :  
    query="select choices.workerid as workerid,games.num as gamenum,"+\
             " decisions.num as decisionnum,decisions.value as decisionval"+\
             " from decisions, choices, rounds, games"+\
             " where decisions.choiceid=choices.id and choices.roundid=rounds.id"+\
             " and rounds.gameid=games.id and rounds.num="+str(EGParameters['numRounds'])+" and decisions.num<"+str(EGParameters['columnNumber'])+\
             " and choices.assignmentid='"+str(assignmentId)+"'"+\
             " order by gamenum,decisionnum,workerid,decisions.timestamp asc"
    cursor.execute(query)
    rows=cursor.fetchall()
    tab_game_lastdecision=dict()
    prev_decisionnum=-1
    for gamenum in range(1,EGParameters['numGames']+1):
      tab_game_lastdecision[gamenum]=dict()
      for decisionnum in range(0,EGParameters['columnNumber']):
        tab_game_lastdecision[gamenum][decisionnum+1]=dict()
    for row in rows:
      if row['decisionnum']!=prev_decisionnum :
        prev_decisionnum=row['decisionnum']
      if(EGParameters['imageType']=='fractal') :
        tab_game_lastdecision[row['gamenum']][row['decisionnum']+1][row['workerid']]=row['decisionval']
      else:
        tab_game_lastdecision[row['gamenum']][row['decisionnum']+1][row['workerid']]=int(row['decisionval'])
    
    # print tab_game_lastdecision
    
    #return render_template('/eg/completed.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId,EGParameters=EGParameters)
    query="select pic_name from gamesets where gamesets.id="+part.assignmentId
    cursor.execute(query)
    row=cursor.fetchone()
    return render_template('/eg/completed.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId,gameset_pic_name=row['pic_name'],
                            tab_userdecision=tab_userdecision,tab_goodresponse=tab_goodresponse,tab_game_lastdecision=tab_game_lastdecision,
                            tab_influencability=tab_influencability, bonus=bonus, rewardcode=keyCodeEnd,EGParameters=EGParameters)
    # 26092016
    """return ('', 204)
     20160503
    return render_template('/eg/login.html',imageType=EGParameters['imageType'],loginValues=loginValues,EGParameters=EGParameters)
    20160503""" 

# 05102016
def influencability(assignmentId,workerId):
  # union add a line at the end of the rows in order to treat the last round of the last game
  query="select choices.workerid as workerid,games.num as gamenum,"+\
           "rounds.num as roundnum,rounds.type as roundtype,decisions.num as decisionnum,decisions.status, decisions.value as decisionval"+\
           " from decisions, choices, rounds, games"+\
           " where decisions.choiceid=choices.id and choices.roundid=rounds.id"+\
           " and rounds.gameid=games.id"+\
           " and choices.assignmentid='"+str(assignmentId)+"'"+\
           " union select 0 as workerid, 1000 as gamenum, 1000 as roudnum, 0 as roundtype, 0 as decisionnum, 0 as status, 1000 as decisionval from decisions"+\
           " order by gamenum,roundnum,decisionnum"
  cursor.execute(query)
  rows=cursor.fetchall()
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
  
  for row in rows :
    if prev_roundnum!=row['roundnum'] and prev_roundnum!=-1:
      if row['roundnum']!=1:# not useful for previous game last round 
        for decisionnum in range(0,EGParameters['columnNumber']):
          sum_of_decision_values=0
          number_of_workerid_decisions=0
          line='roundnum '+str(row['roundnum'])
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
      if row['roundnum']!=2:
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
    if row['gamenum']!=1000 : # last rs line from the union select
      prev_roundnum=row['roundnum']
      tab_lastdecision[row['roundnum']][row['decisionnum']][row['workerid']]=row

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
        query= "update keycode_gameset_user set status='USED',totalreward=0,bonus='"+str(EGParameters['stop_the_gameset_no_other_participant_bonus'])+"'"+\
                  " where userid="+workerId+" and gamesetid="+assignmentId
        cursor.execute(query)
        connection.commit()
        try : # an "internal error" had occured one time during a gameset when selecting the keyCodeEnd, so we check for the exception
          query= "select keyCodeEnd,bonus from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
          cursor.execute(query)
          row=cursor.fetchone()
          keyCodeEnd=row['keyCodeEnd']
          bonus=row['bonus']
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
        query= "select keyCodeEnd,bonus from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
        cursor.execute(query)
        row=rs.fetchone()
        keyCodeEnd=row['keyCodeEnd']
        bonus=row['bonus']
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
          query="update keycode_gameset_user set status="+GetSQLValueString(request.values['newstatusvalue'], 'text')+\
                    ",resultpaycode="+GetSQLValueString('MANUAL', "text")+\
                    ",resultpaymessage="+GetSQLValueString('', "text")+\
                    " where keyCodeBegin="+GetSQLValueString(request.values['keyCodeBegin'], 'text')
          cursor.execute(query)
          connection.commit()
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
                #201411 listOfChoices=[]
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
      # try to catch and correct the exception '2006 Mysql has gone away'
      try :
        query="select count(*) as count from image where status="+str(Image.FREE)+" or status="+str(Image.USED)
        cursor.execute(query)
        row=cursor.fetchone()
      except:
        [connection,cursor,cursor_without_keys]=init_db_connection()
        query="select count(*) as count from image where status="+str(Image.FREE)+" or status="+str(Image.USED)
        cursor.execute(query)
        row=cursor.fetchone()
        #print 'exception 2006 Mysql has gone away'
      EGParameters['totalImagesNumber']=row['count']
      query="select count(*) as count from image where status="+str(Image.FREE)
      cursor.execute(query)
      row=cursor.fetchone()
      EGParameters['freeImagesNumber']=row['count']
      query="select count(*) as count from image where pic_type='fractal'"
      cursor.execute(query)
      row=cursor.fetchone()
      EGParameters['totalfractalImagesNumber']=row['count']
      query="select count(*) as count from image where pic_type='peanut'"
      cursor.execute(query)
      row=cursor.fetchone()
      EGParameters['totalpeanutImagesNumber']=row['count']
      query="select count(*) as count from image where pic_type='fractal'"+" and status="+str(Image.FREE)
      cursor.execute(query)
      row=cursor.fetchone()
      EGParameters['freefractalImagesNumber']=row['count']
      query="select count(*) as count from image where pic_type='peanut'"+" and status="+str(Image.FREE)
      cursor.execute(query)
      row=cursor.fetchone()
      EGParameters['freepeanutImagesNumber']=row['count']
      query= "select count(*) as count from keycode_gameset_user where userid=-1 and gamesetid=-1"
      cursor.execute(query)
      row=cursor.fetchone()
      numFreeKeyCode=row['count']
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
      cursor.execute("select * from games where gameid=1");
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
      img = Image({'pic_name':pic_name,'percent':out[0],'complexity':out[1],'color':out[2],'pic_type':EGParameters['imageType']},'insert')
    else :
      pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
      nbpeanuts = peanuts_light(float(random.randint(200,480))/800,EGParameters['picPath'],EGParameters['estimationPicPath'],pic_name);
      img = Image({'pic_name':pic_name,'percent':nbpeanuts,'complexity':0,'color':'','pic_type':EGParameters['imageType']},'insert')
    
# 11/03/2015
def create_and_select_redundant_images(EGParameters,gamesetid):
  gameset_pic_list=[]
  tab_of_pic=dict()
  image_ordered_list_file=open(os.path.normpath(os.path.abspath(os.path.dirname(__file__))+'/image_ordered_list.csv'))
  numgame=1
  for a_line in image_ordered_list_file:
    game = Game({'num':numgame,'numExpectedParticipants':EGParameters['numExpectedParticipants'],'numRounds':EGParameters['numRounds'],'gamesetid':gamesetid},'insert');
    game_pic_list=[]
    an_ordered_line=a_line.strip("\n")
    index_list=an_ordered_line.split(",")
    for index in index_list:
      index=index.strip()
      if not index in tab_of_pic:
        if EGParameters['imageType'] == 'fractal' :
          pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
          out = fractale_complex(EGParameters['estimationPicPath'],pic_name)
          img = Image({'pic_name':pic_name,'percent':out[0],'complexity':out[1],'color':out[2],'pic_type':EGParameters['imageType']},'insert')
        else :
          pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
          nbpeanuts = peanuts_light(float(random.randint(200,480))/800,EGParameters['picPath'],EGParameters['estimationPicPath'],pic_name);
          img = Image({'pic_name':pic_name,'percent':nbpeanuts,'complexity':0,'color':'','pic_type':EGParameters['imageType']},'insert')
        tab_of_pic[index]=img
      else :
        imgtocopy=tab_of_pic[index]
        img = Image({'pic_name':imgtocopy.pic_name,'percent':imgtocopy.percent,'complexity':imgtocopy.complexity,'color':imgtocopy.color,'pic_type':imgtocopy.pic_type},'insert')
      img.status=Image.USED
      img.gameid=game.id
      img.update()
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
job_id='',# pour test reel job_id='930744', cwf_contributor_id'21619284'
cwf_api_key = 'vir74DJsY4m5Jz6BwcM-',
cwf_timeout=30,
bonusmax='1',# max amount to pay
cwf_displaying_payment='n',
pay_platform='test',
decision_out_of_limit_time=5 # to take in account decisions submitted during the duration of a round but not received after this duration
);
EGParameters['maxpoints_for_10_games']=EGParameters['maxgames']*(EGParameters['socialRoundDuration']+EGParameters['decision_out_of_limit_time'])
if(EGParameters['initDatabase']=='y') :
  confirm=raw_input('Are you sure (y/n):')
  if confirm=='y':
    init_db()
  else:
    print 'Database not initialized'


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
# EGParameters['totalImagesNumber']=Image.query.filter(Image.status == Image.FREE or Image.status == Image.USED).count();
# EGParameters['freeImagesNumber']=Image.query.filter(Image.status == Image.FREE).count();
query="select count(*) as count from image where status="+str(Image.FREE)+" or  status="+str(Image.USED)
cursor.execute(query)
row=cursor.fetchone()
EGParameters['totalImagesNumber']=row['count']
query="select count(*) as count from image where status="+str(Image.FREE)
cursor.execute(query)
row=cursor.fetchone()
EGParameters['freeImagesNumber']=row['count']

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

# gamesetsRunningList : keep data related to gamesets in a dict : avoids db access
gamesetsRunningList=dict();
adminSessionId=''
adminState=''
# perhaps some gamesets, users,... in the db have not been stopped properly : we "clean"   
clean_tables_after_end_on_start()

# pour test reel job_id='930744', cwf_contributor_id'21619284'
# EGParameters['job_id']='paytest1'
# pay_participants(EGParameters)
# cmd_bonus = "curl -X POST --data-urlencode \"amount=" + amount + "\" https://api.crowdflower.com/v1/jobs/930744/workers/"+'21619284'+"/bonus.json?key="+EGParameters['cwf_api_key']
# pour test reel job_id='930744', cwf_contributor_id'21619284'
# from subprocess import check_output
# amount="1"
# cmd_bonus=['curl','-X', 'POST', '--data-urlencode', 'amount='+amount,'https://api.crowdflower.com/v1/jobs/930744/workers/21619284/bonus.json?key='+EGParameters['cwf_api_key']]
# print cmd_bonus
# resultpaymessage = subprocess.check_output(cmd_bonus)
# print resultpaymessage
# # 
# #'21619284'
# out = check_output(['curl','-X', 'POST', '--data-urlencode', '"amount=0"','http://localhost/tests/reponse_wsgi.php'])
# print out

if __name__ == '__main__':
    #try:
      app.run(host=SERVER_HOST, port=EGParameters['serverPort'], debug=SERVER_DEBUG)
    #except:
      #print 'app.run exception'
