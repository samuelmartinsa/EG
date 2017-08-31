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
# our fractale_complex class
from fractale_complex import fractale_complex
from peanuts_light import peanuts_light
# Database setup : our db and models classes
from db import db_session, init_db,free_images,generateNewKeyCodes,connection,engine,\
                get_db_keys_users_gamesets,db_get_free_keys, get_db_users_gamesets,\
                db_get_decision_questionnaire,clean_tables_after_end_on_start,GetSQLValueString,get_EG_session_info,dump_db
from models import Participant, Game, GameSet, Round, Choice, Decision, User, Questionnaire, Code, Image,keycode_gameset_user
# our config class
from config import config

application = app = Flask(__name__)

logfilepath = os.path.join(os.path.dirname(os.path.abspath(__file__)),config.get("Server Parameters", "logfile"))
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
loglevel = loglevels[config.getint('Server Parameters', 'loglevel')]
logging.basicConfig( filename=logfilepath, format='%(asctime)s %(message)s', level=loglevel )


SERVER_HOST = config.get('Server Parameters', 'host')
SERVER_PORT = config.getint('Server Parameters', 'port')
SERVER_DEBUG = config.getboolean('Server Parameters', 'debug')
    
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
  elif request.environ.get('REMOTE_ADDR'):
    ipaddress=request.environ['REMOTE_ADDR']

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
              'timeLeft':str((timeLeft)//60)+'mn '+str((timeLeft)%60)
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
    if(request.form.has_key('keyCodeBegin')):
      givenKeyCodeBegin=string.strip(request.form['keyCodeBegin']);
      # check if keycode exists and is not in a terminated gameset (unused, waiting_for_participants or started)
      query_rs_keyCode="select count(*) as count from keycode_gameset_user"+\
                        " where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text")+\
                        " and keycode_gameset_user.gamesetid not in (select id from gamesets where status=3)"
      rs_keyCode=connection.execute(query_rs_keyCode)
      row_rs_keyCode=rs_keyCode.fetchone()
      if(row_rs_keyCode['count']==1) :
        query_rs_keyCode="select * from keycode_gameset_user where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text")
        rs_keyCode=connection.execute(query_rs_keyCode)
        row_rs_keyCode=rs_keyCode.fetchone()
        userId_of_givenKeyCodeBegin=row_rs_keyCode['userid']
        gameSetId_of_givenCodeKeyCodeBegin=row_rs_keyCode['gamesetid']
      else:
        return render_template('/eg/login.html',flag="KEYCODE_NONEXISTANT_OR_USED",loginValues=loginValues,EGParameters=EGParameters);
    # 05/05/2014
    else:
      return render_template('/eg/login.html',flag="MISSING_KEYCODE",loginValues=loginValues,EGParameters=EGParameters);
    
    # key code exists in db and is not used in a terminated gameset
    # and (EGParameters['activateTimer']=='n' or loginState=='openLogin')   
    if(request.form.has_key('username') and request.form.has_key('pwd') and request.form.has_key('loginsignin')):
      username = request.form['username'];
      password = request.form['pwd']
      if(request.form['loginsignin']=="new"):
        # Check if username exists in database
        matchesUser = User.query.filter(User.username == username).all();
        if(len(matchesUser)==1):
          return render_template('/eg/login.html',flag="ALREADY_IN_DB",loginValues=loginValues,EGParameters=EGParameters);
        elif(len(matchesUser)==0):
          # check for existing IP address (this feature does not work yet because IP is not properly fetch and put in database)
          if(EGParameters['checkIP']=='y'):
            matchesIP = User.query.filter(User.ipaddress == ipaddress).filter(User.ip_in_use=='y').all();
            if(len(matchesIP)>=1):
              return render_template('/eg/login.html',imageType=EGParameters['imageType'],flag="IP_ALREADY_IN_DB",loginValues=loginValues,EGParameters=EGParameters);
          ## end if
          if(userId_of_givenKeyCodeBegin!=-1): #already assigned to an other user
            return render_template('/eg/login.html',flag="KEYCODE_ALREADY_USED",loginValues=loginValues,EGParameters=EGParameters);
          user = NewUser(username,password,ipaddress)#
          user.ip_in_use='y'
          db_session.add(user)
          db_session.commit()
          workerId = str(user.id);
          connection.execute("update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE', usagetime='"+str(datetime.now())+"' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text"))
          assignmentId = "0";
          hitId = "0";
          return render_template('/eg/consent.html',sessionId=user.sessionId, hitId = hitId, assignmentId=assignmentId, workerId=workerId,EGParameters=EGParameters);
        else:
          print "Error, user appears in database more than once (serious problem)"
          raise ExperimentError( 'user_appears_in_database_more_than_once' )
        ## end if
      elif(request.form['loginsignin']=="returning"):                
        matchesUser = User.query.filter(User.username == username).filter(User.password == password).all();
        if(len(matchesUser)==0):# user/password doesn't exist in db
          return render_template('/eg/login.html',flag="AUTH_FAILED",loginValues=loginValues,EGParameters=EGParameters);
        elif(len(matchesUser)==1):
          user = matchesUser[0];
          # Gameset running for this user ?
          query_rs_keyCode="select count(*) as count from keycode_gameset_user, gamesets"+\
                           " where userid="+str(user.id)+" and keycode_gameset_user.gamesetid=gamesets.id"+\
                           " and gamesets.status<>3 and keycode_gameset_user.status='IN_USE'"
          rs_keyCode=connection.execute(query_rs_keyCode)
          row_rs_keyCode=rs_keyCode.fetchone()
          gameset_running_for_user=False
          print "row_rs_keyCode['count']",row_rs_keyCode['count']
          if(row_rs_keyCode['count']>1):
            raise ExperimentError( 'user_has_more_than_one_gameset_not_terminated_and_keycode_in_use' )
          elif(row_rs_keyCode['count']==1):
            gameset_running_for_user=True
            query_rs_keyCode="select * from keycode_gameset_user, gamesets"+\
                             " where userid="+str(user.id)+" and keycode_gameset_user.gamesetid=gamesets.id"+\
                             " and gamesets.status<>3 and keycode_gameset_user.status='IN_USE'"
            rs_keyCode=connection.execute(query_rs_keyCode)
            row_rs_keyCode=rs_keyCode.fetchone()
          if(userId_of_givenKeyCodeBegin==-1):
            print 'userId_of_givenKeyCodeBegin',userId_of_givenKeyCodeBegin
            if(gameset_running_for_user): # gameset running (status=<>3) for the user
              print 'gameset_running_for_user',gameset_running_for_user
              return render_template('/eg/login.html',flag="KEYCODE_GIVEN_WHILE_ANOTHER_IN_USE_FOR_A_NON_TERMINATED_GAMESET",loginValues=loginValues,EGParameters=EGParameters);
            else:
              #print "update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text")
              connection.execute("update keycode_gameset_user set userid="+str(user.id)+",status='IN_USE', usagetime='"+str(datetime.now())+"' where keyCodeBegin="+GetSQLValueString(givenKeyCodeBegin, "text"))
          else:
            print 'gameset_running_for_user',gameset_running_for_user
            if(userId_of_givenKeyCodeBegin==user.id):
              print 'returning user in its gameset : ',gameSetId_of_givenCodeKeyCodeBegin
            else:
              return render_template('/eg/login.html',flag="KEYCODE_ALREADY_USED",loginValues=loginValues,EGParameters=EGParameters);
          user.ipaddress = ipaddress
          user.lastvisit = datetime.now();
          user.sessionId = random.randint(10000000, 99999999);
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
        # end if(len(matchesUser)==0)elif((len(matchesUser)==1)
      # end elif(request.form['loginsignin']=="returning") 
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

def NewUser(username,password,ipaddress):#
    user = User();
    user.username = username;
    user.password = password;
    user.ipaddress=ipaddress
    user.lastvisit = datetime.now();
    user.sessionId = random.randint(10000000, 99999999);
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
        to_return = render_template('/eg/login.html',flag="SESSION_EXPIRED",loginValues=loginValues,EGParameters=EGParameters);        
    return [hitId,assignmentId,workerId,user,to_return]

@app.route('/eg/consent', methods=['GET','POST'])
def give_consent():
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    hitId = 0;
    assignmentId = 0;
    if to_return!=None:
        return to_return;    
        
    if(request.method == "POST" and request.form.has_key('consented') and request.form['consented']):
        user.status = User.CONSENTED
        db_session.add(user)
        db_session.commit()
    
    res = redirect(user,hitId,assignmentId,workerId,user.sessionId)
    return res

def findParticipant(hitId,assignmentId,workerId,addIfNotFound):
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
            db_session.add( part )
            db_session.commit()
            #print 'Participant added in database'
            return part
        else:
            return False
    elif numrecs == 1:
        return matches[0]
    else:
        print "Error, hit/assignment appears in database more than once (serious problem)"
        raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )

def findUser(workerId):
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
  if EGParameters['skipConsentInstruct']=='y' :
    user.status=User.INSTRUCTED
    db_session.add(user)
    db_session.commit()
    return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,EGParameters=EGParameters) 
  else :
    if(not user or user.status == User.ALLOCATED):
        return render_template('/eg/consent.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,EGParameters=EGParameters)
    elif(user.status == User.CONSENTED):
        return render_template('/eg/questionnaire_first.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,EGParameters=EGParameters)    
    elif(user.status == User.ASSESSED):
        return render_template('/eg/instruct.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,EGParameters=EGParameters) 
    elif(user.status == User.INSTRUCTED):
        return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId,EGParameters=EGParameters) 
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
    currentGamesets = GameSet.query.join(Participant.gamesets)\
                            .filter(Participant.workerId == str(user.id))\
                            .filter(GameSet.status!=GameSet.TERMINATED).all()
    if len(currentGamesets)== 0:# user not in a current gameset
        # assign a gameset to the participant        
        vacantGameSets = db_session.query(GameSet.id,func.count(GameSet.id),GameSet.numExpectedParticipants,Participant.workerId,Participant.assignmentId).\
                join((Participant,GameSet.participants)).\
                group_by(GameSet.id).\
                having(func.count(GameSet.id)<GameSet.numExpectedParticipants)
        
        #print 'Number of vacant games:',vacantGameSets.all(),print vacantGameSets.count()
        if(vacantGameSets.count()==0):# new gameset
            gameset = GameSet();
            gameset.numExpectedParticipants = EGParameters['numExpectedParticipants'];
            gameset.numGames=EGParameters['numGames'];
            gameset.starttime=datetime.now();
            gameset.playmode=EGParameters['playMode'];
            db_session.add( gameset )
            db_session.commit()
            
            #creation of the part : link between user and gameset
            addIfNotFound = True # added in consent only
            part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)
            
            part.gamesets.append(gameset);            
            
            game = Game(EGParameters['imageType']);
            game.num = 1;
            game.numExpectedParticipants = gameset.numExpectedParticipants;
            game.numRounds=EGParameters['numRounds'];
            #print 'game.numExpectedParticipants', game.numExpectedParticipants
            #game.numGames=EGParameters['numGames'];
            gameset.games.append(game);
            part.games.append(game);
            db_session.add( game )
            db_session.commit()
            
            hidId = str(gameset.id);
            assignmentId = str(gameset.id);            
            part.hitId = hidId;
            part.assignmentId = assignmentId;
            db_session.commit()
            #query_rs_keyCode="update keycode_gameset_user set gamesetid="+str(gameset.id)+\
            #                   " where userid="+str(user.id)+" and status='IN_USE' and gamesetid=-1"
            #connection.execute(query_rs_keyCode)

        else:# gameset exists : user added as a participant in the gameset
            gamesetTuple = vacantGameSets.order_by(func.count('*').desc()).first()
            gameset = db_session.query(GameSet).get(gamesetTuple[0])
            
            #retrieval of the part : link between user and gameset
            addIfNotFound = True # added in consent only
            part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)            
            if(not part):
                raise ExperimentError('participant_not_found_gameset_exists_waiting_room')
            part.gamesets.append(gameset)            
            game = db_session.query(Game).filter(Game.num==1).join(GameSet.games).filter(Game.gamesetid == gameset.id).one(); 
            part.games.append(game)
            db_session.commit()
        query_rs_keyCode="select count(*) as count from keycode_gameset_user"+\
                           " where userid="+str(user.id)+" and  status='IN_USE' and gamesetid=-1"
        rs_keyCode=connection.execute(query_rs_keyCode)
        row_rs_keyCode=rs_keyCode.fetchone()
        if(row_rs_keyCode['count']==1):
          query_rs_keyCode="update keycode_gameset_user set gamesetid="+str(gameset.id)+\
                          " where userid="+str(user.id)+" and  status='IN_USE' and gamesetid=-1"
          connection.execute(query_rs_keyCode)
        else:
          raise ExperimentError('user_has_0_or_more_than_1_keycode_in_use')
    elif (len(currentGamesets)== 1):# user in a non terminated gameset
        gameset = currentGamesets[0];
        #retrieval of the part : link between user and gameset
        addIfNotFound = False # added in consent only
        part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)
        if(not part):
            raise ExperimentError('participant_not_found_gameset_exists_waiting_room')
    else:
        print "Error, participant has started more than one game at the same time"
        raise ExperimentError('part_has_more_than_one_started_game')
                
    numParticipants = len(gameset.participants);
    workerId = part.workerId
    assignmentId = part.assignmentId
    hitId = part.hitId
    sessionId = user.sessionId
    
    if(gameset.numExpectedParticipants > numParticipants):#not enough participants
        if (request.args.has_key('getFlag')):
          return json.dumps({'activateTimer':EGParameters['activateTimer'],'status':'Wait_in_room','missingParticipant':str(gameset.numExpectedParticipants - numParticipants), 'timeLeft':str(leftDelayToBeginGameSet//60)+'mn '+str(leftDelayToBeginGameSet%60)})
        else:
          return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, sessionId=sessionId, workerId=workerId, missingParticipant=str(gameset.numExpectedParticipants - numParticipants),EGParameters=EGParameters)
    elif(gameset.numExpectedParticipants == numParticipants):#enough participants
        gameset.status = GameSet.STARTED
        db_session.commit()
        if (request.args.has_key('getFlag')):
            return json.dumps({'status':'GameSet_STARTED'})
        else:
            return start_exp_consensus(part)
    else:
        raise ExperimentError( 'too_many_participants' )
                
@app.route('/eg/intermediatepage', methods=['GET'])
def intermediate():
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=user.sessionId,EGParameters=EGParameters)
            

@app.route('/eg/expconsensus', methods=['GET','POST'])
def start_exp_consensus(part = None):
  # timeout for continuous mode : SOCIAL round stops on timeout, not on sent values from participants
  # continuousListOfDecisions : decisions taken by the current participant
  # In continuous mode, we should work just with 1 image, not 3 like in discrete mode
  # But it's easier to write code with 3 decisions like in discrete mode, so we currently work with 3 decisions corresponding to 3 images
  # In expconsensus.html, 3 decisions are sent : 2 are in hidden fields
  timeout=False
  global continuousListOfChoices,continuousListOfDecisions#,isNewExpconsensusRound
  #print 'deb exp isNewExpconsensusRound',isNewExpconsensusRound
  continuousListOfDecisions=[0,0,0]
  prevRoundChoicesSortedList=[]
  # check first to see if this hitId or assignmentId exists.  if so check to see if inExp is set
  if(part==None):#try to set part
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:#print "returning to login"
      return to_return
    #print 'starting experiment consensus',hitId, assignmentId, workerId
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
    return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId)
  gameset = part.gamesets[0];#gamesets[0] is the unique gameset of a participant
  curgame = db_session.query(Game).join(GameSet).filter(Game.gamesetid==gameset.id).filter(gameset.curGameNum()==Game.num).one()
  numParticipants = len(gameset.participants);
  if(gameset.numExpectedParticipants > numParticipants):
    # Preventing trouble
    return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, missingChoices=str(gameset.numExpectedParticipants - numParticipants),sessionId=user.sessionId,EGParameters=EGParameters)
  elif(gameset.numExpectedParticipants < numParticipants):
    raise ExperimentError( 'too_many_participants' )
  
  # Start the experiment = gameset.numExpectedParticipants == numParticipants
  imageurl = [];
  if(Image.query.filter(Image.pic_type==EGParameters['imageType']).count()<3):
    raise ExperimentError('insuffisant_image_number')
  imageurl.append(estimationPicPath+str(curgame.image[0].pic_name))
  imageurl.append(estimationPicPath+str(curgame.image[1].pic_name))
  imageurl.append(estimationPicPath+str(curgame.image[2].pic_name))

  if EGParameters['imageType']=='fractal' :
    if EGParameters['playMode']=='discrete' :
      question="What is the colour percentage in each image?"
    else :
      question="What is the colour percentage in the image?"
  else :
    if EGParameters['playMode']=='discrete' :
      question="How many peanuts do you see in each image?"
    else :
      question="How many peanuts do you see in the image?"
  color = [];
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
                            'staticPath' : staticPath,
                            'playMode' : EGParameters['playMode'],
                            'columnNumber' : EGParameters['columnNumber'],
                            'loneMaxReward' : EGParameters['loneMaxReward'],
                            'socialMaxReward' : EGParameters['socialMaxReward'],
                            }
  
  if(len(request.form)>0 and not request.form.has_key('No decision')):#form sent without field 'No decision'
    curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curgame.curRoundNum()==Round.num).one()
    # Add the participant new choice and decisions
    expconsensusAttributes['round']=curgame.curRoundNum();
    #print "not isChoiceMade(curround,part):",not isChoiceMade(curround,part),"curround.num == int(request.form['roundNum'])",curround.num, '==', int(request.form['roundNum'])
    # PG if(not isChoiceMade(curround,part) and curround.num == int(request.form['roundNum'])):
    if((not isChoiceMade(curround,part) or EGParameters['playMode']=='continuous') and curround.num == int(request.form['roundNum'])):
      decision0Value = request.form['decision0']
      decision1Value = request.form['decision1']
      decision2Value = request.form['decision2']
      auto0 = request.form['auto0']
      auto1 = request.form['auto1']
      auto2 = request.form['auto2']
      # if auto==1, auto_reg=Decision.AUTO which value=2 in DB table decisions !!! else auto_reg=Decision.USER_MADE which value=1 in DB table decisions
      if int(auto0)==1:
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
          continuousListOfChoices[0][int(part.workerId)-1]=float(decision0Value) 
          continuousListOfDecisions=[float(decision0Value),float(decision1Value),float(decision2Value)]
        else :
          continuousListOfChoices[0][int(part.workerId)-1]=int(decision0Value)  
          continuousListOfDecisions=[int(decision0Value),int(decision1Value),int(decision2Value)]
        ## end if
        # if testMode, generate a random choice for a simulated participant
        if (EGParameters['testMode']=='y' and curround.type==Round.SOCIAL) :
          randomSimulatedParticipant=random.randint(EGParameters['numExpectedParticipants'],EGParameters['numExpectedParticipants']+EGParameters['numSimulatedParticipants']-1)
          continuousListOfChoices[0][randomSimulatedParticipant]=random.randint(int(EGParameters['minDecisionValue']),int(EGParameters['maxDecisionValue']))
        ## end if
      ## end if
      # continuous version, suitable for discrete case :  distinct participants number in choices for this round
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
    else: #Decision but no choice made
      if(curround.num != int(request.form['roundNum'])):
          print "Problem : posting probably from old round to current round"
          print "This may be due to server lag. Aborting decision making. curround.num=",curround.num ,"request.form['roundNum']",request.form['roundNum']                                                                                                                                                                                  
      ## end if
    ## end if
  ##end if form sent without field 'No decision'
  if(curgame.curRoundNum()==0):# Setting the first round
    curround = Round();
    curround.num = 1;
    curround.type = Round.LONE;
    curround.maxreward = EGParameters['loneMaxReward'];                            
    curround.status = Round.STARTED
    curround.startTime = datetime.now()
    curgame.rounds.append(curround)                                                                    
    db_session.commit()
  ## end if  
  # curgame and curround are ready  
  curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curgame.curRoundNum()==Round.num).one()
  expconsensusAttributes['round']=curgame.curRoundNum();
  expconsensusAttributes['game']=len(part.games);
  if(curgame.curRoundNum()>1):# SOCIAL rounds
    # Past estimation to display : from previous round number or from same round number if continuous                                          
    if(EGParameters['playMode']=='discrete') :#discrete SOCIAL
      prevround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(Round.num==curgame.curRoundNum()-1).one()
      prevchoice = db_session.query(Choice).filter(Choice.workerId == workerId and Choice.assignmentId == assignmentId).join(Round).join(Game).filter(Round.gameid==curgame.id).filter(Round.num==curgame.curRoundNum()-1).one()
      listprevround = prevround.listOfChoices()
      listprevchoice = prevchoice.listOfDecisions()
    else : #continuous SOCIAL
      # SOCIAL round estimations have been registered in database for the current round or in the previous LONE round  
      # look for LONE last decisions in LONE round or in this SOCIAL curround
      # prevchoice = db_session.query(Choice).filter(Choice.workerId == workerId and Choice.assignmentId == assignmentId).join(Round).join(Game).filter(Round.gameid==curgame.id).filter(Round.num==curgame.curRoundNum()-1).one()
      listprevround=continuousListOfChoices
      listprevchoice = continuousListOfDecisions
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
  all_serious_workers_have_chosen=False
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
    query_rs="select choices.workerId, sum(decisions.status) as sumstatus"+\
              " from games,rounds,choices,decisions"+\
              " where games.id=rounds.gameid and rounds.id=choices.roundid"+\
              " and choices.id=decisions.choiceid"+\
              " and ((games.num="+str(gamenum_previous)+" and rounds.num="+str(roundnum_previous)+") or (games.num="+str(gamenum_previous_previous)+" and rounds.num="+str(roundnum_previous_previous)+"))"+\
              " and games.gamesetid="+str(gamesetid)+\
              " group by workerId"+\
              " order by 0+choices.workerId";
    rs=connection.execute(query_rs)
    for row_rs in rs:
      a_workerId=row_rs[0]
      sumstatus=int(row_rs[1])
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
  # end looking for "serious" participants have already sent their decision in this round
  
  # remaining time out of limit : Register choices automatically for participants without choice made in the current game of the curround
  # or "serious" participants have already sent their decision in this round
  if(remainingTime<timedelta(days=0,seconds=-15) or remainingTime>timedelta(days=0,seconds=1000) or all_serious_workers_have_chosen):
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
      missingChoices = len(curgame.participants)-len(curround.choices)
    else:
      # continuous version : distinct participants number in choices for this round
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
      
  curgame = db_session.query(Game).join(GameSet).filter(Game.gamesetid==gameset.id).filter(gameset.curGameNum()==Game.num).one()
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
    distinctParticipantsListChoiceInRound=db_session.query(distinct("'"+Choice.roundid+"::"+Choice.assignmentId+"::"+Choice.workerId)).filter(Choice.roundid==curround.id) 
    missingChoices = len(curgame.participants)-distinctParticipantsListChoiceInRound.count() 
    # before continuous version : missingChoices = len(curgame.participants)-len(curround.choices)
    expconsensusAttributes['missingChoices'] = str(missingChoices)
    # before continuous version : if(missingChoices==0 and curround.num == curgame.numRounds):
    if(missingChoices==0 and curround.num == curgame.numRounds and (curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout)):
      #print 'if(missingChoices==0 and curround.num == curgame.numRounds)'
      #print "Game over in the wrong way"
      if(gameset.curGameNum()==gameset.numGames):
        #print "Game set is over"
        expconsensusAttributes['status'] = "GAMESET_OVER"
        gameset.status = GameSet.TERMINATED;
        curgame.status = Game.TERMINATED;
        db_session.commit()
      else:
        #if(curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout):
          #print "if(curround.type==Round.LONE or EGParameters['playMode']=='discrete' or timeout)"
          expconsensusAttributes['status'] = "GAME_OVER"
          curgame.status = Game.TERMINATED;
          newgame = Game(EGParameters['imageType']);
          newgame.num = curgame.num+1;
          newgame.numRounds=EGParameters['numRounds'];
          newgame.numExpectedParticipants = gameset.numExpectedParticipants;
          gameset.games.append(newgame);
          for each_part in gameset.participants:
            each_part.games.append(newgame);
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
  
  if (request.args.has_key('getFlag')): # In Update : answer to the get periodical send by in expconsensus.html with js timer setInterval 
    #isNewExpconsensusRound[int(part.workerId)-1]='False'
    return json.dumps(expconsensusAttributes)
  else: # Not In Update : post made with expconsensus
    expconsensusAttributes['sessionId']=user.sessionId
    return render_expconsensus(part,**expconsensusAttributes)
    #return render_template('/eg/expconsensus.html', **expconsensusAttributes) 
  ##end if

def render_expconsensus(part,**expconsensusAttributes):
    if(part.status < Participant.STARTED):
        part.status=Participant.STARTED
        expconsensusAttributes['sound']=1
    else:
        expconsensusAttributes['sound']=0
    return render_template('/eg/expconsensus.html',EGParameters=EGParameters, **expconsensusAttributes)
        
def terminateRound(curround,curgame,gameset) :
  # 16/03 init decisions to 0 if end of game
  global continuousListOfChoices,continuousListOfDecisions
  global EGParameters#,isNewExpconsensusRound
  """isNewExpconsensusRound=[]          
  for i in range(0,EGParameters['numExpectedParticipants']):
    isNewExpconsensusRound.append("True")"""
  curround.status=Round.TERMINATED;
  htmlStatus = "";
  if(curround.num==curgame.numRounds):
    curgame.status = Game.TERMINATED;
    if(gameset.curGameNum()==gameset.numGames):
      htmlStatus = "GAMESET_OVER"
      gameset.status = GameSet.TERMINATED;
      curgame.status = Game.TERMINATED;
    else:
      htmlStatus = "GAME_OVER"
      curgame.status = Game.TERMINATED;
      newgame = Game(EGParameters['imageType']);
      newgame.num = curgame.num+1;
      newgame.numRounds=EGParameters['numRounds'];
      newgame.numExpectedParticipants = gameset.numExpectedParticipants;
      gameset.games.append(newgame);
      for each_part in gameset.participants:
        each_part.games.append(newgame);
      curround = startNewRound(newgame)
      db_session.commit()
    
      # 16/03 init
      continuousListOfChoices=[]   
      continuousListOfDecisions=[0,0,0]
      for i in range(0,3):
        initlist=[]
        for j in range(0,EGParameters['numExpectedParticipants']+EGParameters['numSimulatedParticipants']):
          initlist.append(0)
        # end for
        continuousListOfChoices.append(initlist)
      # end for
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
        curround.maxreward = EGParameters['loneMaxReward'];
    else:
        curround.type = Round.SOCIAL; 
        curround.maxreward = EGParameters['socialMaxReward'];                               
    curround.status = Round.STARTED
    curround.startTime = datetime.now()
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
    # currently percent contains a percent or a number such as for peanuts
    # print 'registerChoice decisions : ',decision0.value,decision1.value,decision2.value,curround.game.image[0].percent,curround.game.image[1].percent,curround.game.image[2].percent
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
    curround.choices.append(choice)
    part.choices.append(choice)
    db_session.commit()
    while(not isChoiceMade(curround,part)):
        pass
        
def reward(errorsize,maxreward):
    if(errorsize<2):
        weight = 1;
    elif(errorsize<5):
        weight = 0.5;
    elif(errorsize<15):
        weight = 0.2;
    else:
        weight = 0;

    return weight*maxreward;
        
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
    print request.form.keys()
    if request.form.has_key('assignmentId') and request.form.has_key('dataString'):
        assignmentId = request.form['assignmentId']
        datastring = request.form['dataString']  
        print "getting the save data", assignmentId, datastring
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
def savedata():
    """
    User has finished the experiment and is posting their data in the form of a
    (long) string. They will receive a debriefing back.
    """
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
    total = 0;
    for choice in part.choices:
        for decision in choice.decisions:
            if(decision.status==Decision.USER_MADE):
                total = total + decision.reward;
                 
    part.status = Participant.COMPLETED
    user.endhit = datetime.now()
    db_session.add(user)
    db_session.commit()
    rewardCode = 0
    for code in user.codes:
        if code.status==Code.FREE:
            rewardCode = code.value
            code.status=Code.USED
            db_session.commit()
            break
    query_rs_keyCode= "update keycode_gameset_user set status='USED',totalreward="+str(total)+\
                      " where userid="+workerId+" and gamesetid="+assignmentId
    
    connection.execute(query_rs_keyCode)
    
    query_rs_keyCode= "select keyCodeEnd from keycode_gameset_user where userid="+workerId+" and gamesetid="+assignmentId
    rs_keyCode=connection.execute(query_rs_keyCode)
    row_rs_keyCode=rs_keyCode.fetchone()
    email=user.email
    if email==None:
      email=''
    return render_template('/eg/debriefing.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId, totalreward=total, rewardcode=row_rs_keyCode['keyCodeEnd'],email=email)

@app.route('/eg/complete', methods=['POST'])
def completed():
    """
    This is sent when the participant completes the debriefing. The
    participant can accept the debriefing or declare that they were not
    adequately debriefed, and that response is logged in the database.
    """
    loginValues={'keyCodeBegin':'','username':'','loginsignin':'','pwd':'','pwd2':''};    
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
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
    return render_template('/eg/login.html',imageType=EGParameters['imageType'],loginValues=loginValues,EGParameters=EGParameters)


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
        game = Game(EGParameters['imageType']);
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
  global continuousListOfChoices
  EGDBContent=dict();
  error="You have to connect before!"#default
  if request.values.has_key('sessionId'):
    if request.values['sessionId']==adminSessionId :
      if request.method == 'POST':
        if request.values.has_key('newstatusvalue') and request.values.has_key('keyCodeBegin'):
          query_rs="update keycode_gameset_user set status="+GetSQLValueString(request.values['newstatusvalue'], 'text')+" where keyCodeBegin="+GetSQLValueString(request.values['keyCodeBegin'], 'text')
          connection.execute(query_rs)
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
  if request.values.has_key('sessionId'):
    if request.values['sessionId']==adminSessionId :  
      if request.values.has_key('what'):
        what=request.values['what']
        if what=='db_get_decision_questionnaire' :
          res=db_get_decision_questionnaire()
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
  global continuousListOfChoices, continuousListOfDecicions#,isNewExpconsensusRound
  global connection
  connection = engine.connect()
  db_users_gamesets=dict()
  numFreeKeyCode=""
  loginError = ''
  warning=''
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
          if request.form.has_key('submitstop') :
            EGParameters['EGRunning']=False;
            continuousListOfChoices=[]
            continuousListOfDecicions=[]
          elif request.form.has_key('submitstart') :
            """for one_EGParameter in EGParameters :
              if request.form.has_key(one_EGParameter): 
                EGParameters[one_EGParameter]=request.form[one_EGParameter]
            ## end for"""
            """if request.form.has_key('initDatabase') and request.form['initDatabase']=='y' :
              init_db()
            ## end if"""
            nowDate = datetime.utcnow()
            EGParameters['starttimeutc']=nowDate
            try :
              if request.form.has_key('starthour') :
                try:
                  EGParameters['starthour']=request.form['starthour']
                  EGParameters['nextGameDate']=nowDate+timedelta(hours=int(list(split(EGParameters['starthour'],':'))[0]),minutes=int(list(split(EGParameters['starthour'],':'))[1]))
                  print "EGParameters['nextGameDate']",EGParameters['nextGameDate']
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
              if request.form.has_key('activateTimer') :
                EGParameters['activateTimer']='y'
              else:
                EGParameters['activateTimer']='n'
              if request.form.has_key('checkIP') :
                EGParameters['checkIP']='y'
              else:
                EGParameters['checkIP']='n'
              if request.form.has_key('imageType') :
                EGParameters['imageType']=request.form['imageType']
                if EGParameters['imageType'] == 'fractal' :
                  EGParameters['minDecisionValue']='0.0'
                  EGParameters['maxDecisionValue']='100.0' 
                elif EGParameters['imageType'] == 'peanut' :
                  EGParameters['minDecisionValue']='0'
                  EGParameters['maxDecisionValue']='500'
              ## end if
              if request.form.has_key('numRounds') :
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
              if EGParameters['playMode']=='discrete' :
                EGParameters['columnNumber']=3
              else :#continuous
                EGParameters['columnNumber']=1
                EGParameters['numRounds']=2
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
              if request.form.has_key('loneMaxReward') :
                try:
                  EGParameters['loneMaxReward']=int(request.form['loneMaxReward'])
                except:
                  warning=warning+'Reward... not int.'
              if request.form.has_key('socialMaxReward') :
                try:
                  EGParameters['socialMaxReward']=int(request.form['socialMaxReward'])
                except:
                  warning=warning+'Reward... not int.'
              EGParameters['ratioForErrorSize']=(float(EGParameters['maxDecisionValue'])-float(EGParameters['minDecisionValue']))/100
              if request.form.has_key('numExpectedParticipants') :
                try:
                  EGParameters['numExpectedParticipants']=int(request.form['numExpectedParticipants'])
                  continuousListOfChoices=[]
                  for i in range(0,3):
                    initlist=[]
                    for j in range(0,EGParameters['numExpectedParticipants']):
                      initlist.append(0)
                    continuousListOfChoices.append(initlist)
                  ## end for
                except:
                  warning=warning+'Participants... not int.'
              ## end if
              if request.form.has_key('testMode'):
                EGParameters['testMode']=request.form['testMode']
                EGParameters['numSimulatedParticipants']=0
                if EGParameters['testMode']=='y' and EGParameters['playMode']=='continuous':
                  continuousListOfChoices=[]
                  EGParameters['numSimulatedParticipants']=max(12-EGParameters['numExpectedParticipants'],0)
                  for i in range(0,3):
                    initlist=[]
                    for j in range(0,EGParameters['numExpectedParticipants']+EGParameters['numSimulatedParticipants']):
                      initlist.append(0)
                    continuousListOfChoices.append(initlist)
                  ## end for
              ## end if
              if request.form.has_key('skipConsentInstruct'):
                EGParameters['skipConsentInstruct']=request.form['skipConsentInstruct']
              if request.form.has_key('numNewKeyCodes'):
                try:
                  EGParameters['numNewKeyCodes']=int(request.form['numNewKeyCodes'])
                except:
                  warning=warning+'Key codes... not int.'
              ## end if
              if warning=='':
                clean_tables_after_end_on_start()
                EGParameters['EGRunning']=True;
                generateImages(EGParameters)
                if request.form.has_key('freeImages') and request.form['freeImages']=='y' :
                  free_images()
                if(EGParameters['numNewKeyCodes'])>0:
                  generateNewKeyCodes(EGParameters['numNewKeyCodes'])
                continuousListOfChoices=[]
                continuousListOfDecicions=[]
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
        if request.form['username']=='admin' and request.form['pwd']=='admin':
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
                        'activateTimer':EGParameters['activateTimer'],
                        'loginState':loginState,
                        'timeLeft':str((timeLeft)//60)+'mn '+str((timeLeft)%60),
                        'gameSetState':gameSetState,
                        'EG_session_info':get_EG_session_info(EGParameters)
                       }
      return json.dumps(adminAttributes)
    else:
      EGParameters['totalImagesNumber']=Image.query.count();
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
      return render_template('/eg/admin.html',adminState=adminState, sessionId=adminSessionId,warning=warning, EGParameters=EGParameters,numFreeKeyCode=numFreeKeyCode)
   
def generateImages(EGParameters):
  # generate n images and store them in the database
  i=0
  for i in  range(1,EGParameters['numImages']+1):#range(1,numImages+1)
    if EGParameters['imageType'] == 'fractal' :
      pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
      out = fractale_complex(EGParameters['estimationPicPath'],pic_name)
      img = Image(pic_name,out[0],out[1],out[2],EGParameters['imageType'])
      print pic_name
    else :
      pic_name=str(datetime.now().strftime('%Y%m%d-%H%M%S-%f'))+'.png'
      nbpeanuts = peanuts_light(200,499,EGParameters['picPath'],EGParameters['estimationPicPath'],pic_name);
      print pic_name
      img = Image(pic_name,nbpeanuts,'',0,EGParameters['imageType'])
    db_session.add(img)
    db_session.commit()
  print str(i)+' images generated.'

#----------------------------------------------------------
# Variables and default values
#----------------------------------------------------------
staticPath="/static/"
tmpPath=staticPath+"tmp/"
picPath = staticPath+"pic/"# base pictures path
estimationPicPath = picPath+"estimationPic/" # pictures for estimations
tmpPicPath= picPath+"tmp/"# pictures generated during rounds. They can be deleted after a game set

parser = argparse.ArgumentParser(description='Estimation game')
parser.add_argument('-p','--serverPort',  help='Application http port (default='+str(SERVER_PORT)+')', default=SERVER_PORT)
parser.add_argument('-i','--initDatabase', choices=['y', 'n'],  help='Initialize database (default=n)', default='n')
args = parser.parse_args()

EGParameters = dict(EGRunning=False,initDatabase=args.initDatabase,serverPort=args.serverPort,playMode='discrete',
imageType = 'peanut',freeImages='n',numImages=6,loneRoundDuration=20,socialRoundDuration=20,loneMaxReward=5,socialMaxReward=10,
numExpectedParticipants=1,numGames=1,numRounds=2,numNewKeyCodes=1,testMode='n',skipConsentInstruct='n',activateTimer='n'
);
EGParameters['staticPath']="/static/"
EGParameters['tmpPath']=staticPath+"tmp/"
EGParameters['picPath'] = staticPath+"pic/"# base pictures path
EGParameters['estimationPicPath'] = picPath+"estimationPic/" # pictures for estimations
EGParameters['tmpPicPath']= picPath+"tmp/"# pictures generated during rounds. They can be deleted after a game set

EGParameters['activateTimer']='y'
EGParameters['starthour']='0:10'
nowDate = datetime.utcnow()
EGParameters['starttimeutc']=nowDate
EGParameters['nextGameDate']=nowDate+timedelta(hours=int(list(split(EGParameters['starthour'],':'))[0]),minutes=int(list(split(EGParameters['starthour'],':'))[1]))
EGParameters['maxDelayToLoginGameSet']=4 # minutes
EGParameters['maxDelayToBeginGameSet']=10 # minutes
loginAttributes={'EGRunning':EGParameters['EGRunning'],'timeLeftBeforeGameSet':(nowDate-EGParameters['nextGameDate']).total_seconds()}
EGParameters['checkIP']='y'
if(EGParameters['initDatabase']=='y') :
  confirm=raw_input('Are you sure (y/n):')
  if confirm=='y':
    init_db()
  else:
    print 'Database not initialized'
connection = engine.connect()

continuousListOfChoices=[]
continuousListOfDecicions=[]
#isNewExpconsensusRound=[]  used for expconsensus : if True, expconsensus will refresh estimation images
EGParameters['numSimulatedParticipants']=0
if EGParameters['testMode']=='y' and EGParameters['playMode']=='continuous' :
  EGParameters['numSimulatedParticipants']=max(12-EGParameters['numExpectedParticipants'],0)
  for i in range(0,3):
    initlist=[]
    for j in range(0,EGParameters['numExpectedParticipants']+EGParameters['numSimulatedParticipants']):
      initlist.append(0)
    continuousListOfChoices.append(initlist)

if EGParameters['playMode']=='discrete' :
  EGParameters['columnNumber']=3
else :#continuous
  EGParameters['columnNumber']=1
  EGParameters['numRounds']=2
## end if 
EGParameters['numImages']=EGParameters['numGames']*EGParameters['columnNumber']
EGParameters['totalImagesNumber']=Image.query.count();
EGParameters['freeImagesNumber']=Image.query.filter(Image.status == Image.FREE).count();

if EGParameters['imageType'] == 'fractal' :
  EGParameters['minDecisionValue']='0.0'
  EGParameters['maxDecisionValue']='100.0' 
elif EGParameters['imageType'] == 'peanut' :
  EGParameters['minDecisionValue']='0'
  EGParameters['maxDecisionValue']='500'
EGParameters['ratioForErrorSize']=(float(EGParameters['maxDecisionValue'])-float(EGParameters['minDecisionValue']))/100

adminSessionId=''
adminState=''
#dump_db(EGParameters['tmpPath'])

if __name__ == '__main__':
    #try:
      app.run(host=SERVER_HOST, port=EGParameters['serverPort'], debug=SERVER_DEBUG)
    #except:
      #print 'app.run exception'