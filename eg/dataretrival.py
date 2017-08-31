from flask import abort, send_file
from datetime import datetime, timedelta
import sys
import os
import json
import logging
import traceback
import site
import random
from distutils.sysconfig import get_python_lib
from functools import wraps

# Database setup
from db import db_session, init_db, engine
from models import Participant, Game, GameSet, Round, Choice, Decision, User, Questionnaire, Image
from sqlalchemy import or_, sql
from sqlalchemy.sql.expression import func 

from config import config

from flask import Flask, render_template, request, Response, make_response
import sqlalchemy
application = app = Flask(__name__)

logfilepath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           config.get("Server Parameters", "logfile"))

loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
loglevel = loglevels[config.getint('Server Parameters', 'loglevel')]
logging.basicConfig( filename=logfilepath, format='%(asctime)s %(message)s', level=loglevel )

# constants
USING_SANDBOX = config.getboolean('HIT Configuration', 'using_sandbox')
CODE_VERSION = config.get('Task Parameters', 'code_version')

# Database configuration and constants
TABLENAME = config.get('Database Parameters', 'table_name')
SUPPORTIE = config.getboolean('Server Parameters', 'support_IE')

#----------------------------------------------
# function for authentication
#----------------------------------------------
queryname = config.get('Server Parameters', 'login_username')
querypw = config.get('Server Parameters', 'login_pw')

SERVER_HOST = config.get('Server Parameters', 'host')
SERVER_PORT = config.getint('Server Parameters', 'port')
SERVER_DEBUG = config.getboolean('Server Parameters', 'debug')


def wrapper(func, args):
    return func(*args)

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == queryname and password == querypw

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    """
    Decorator to prompt for user name and password. Useful for data dumps, etc.
    that you don't want to be public.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

    
    
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
    page_not_found = 404,
    in_debug = 2005,
    unknown_error = 9999
)


class ExperimentError(Exception):
    """
    Error class for experimental errors, such as subject not being found in
    the database.
    """
    def __init__(self, value):
        self.value = value
        self.errornum = experiment_errors[self.value]
    def __str__(self):
        return repr(self.value)
    def error_page(self, request):
        return render_template('/eg/error.html', 
                               errornum=self.errornum, 
                               **request.args)

@app.errorhandler(ExperimentError)
def handleExpError(e):
    """Handle errors by sending an error page."""
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
def get_people(people):
    if not people:
        return []
    for record in people:
        person = {}
        for field in ['ipaddress', 'hitId', 'assignmentId',
                      'workerId', 'cond', 'counterbalance',
                      'beginhit','beginexp', 'endhit', 'status', 'datastring']:
            if field=='datastring':
                if record[field] == None:
                    person[field] = "Nothing yet"
                else:
                    person[field] = record[field][:10]
            else:
                person[field] = record[field]
        people.append( person )
    return people



#----------------------------------------------
# routes
#----------------------------------------------
@app.route('/eg/mturk', methods=['GET'])
def mturkroute():
    """
    This is the url we give for our 'external question'.
    This page will be called from within mechanical turk, with url arguments
    hitId, assignmentId, and workerId. 
    If the worker has not yet accepted the hit:
      These arguments will have null values, we should just show an ad for the
      experiment.
    If the worker has accepted the hit:
      These arguments will have appropriate values and we should enter the person
      in the database and provide a link to the experiment popup.
    """
    if not SUPPORTIE:
        # Handler for IE users if IE is not supported.
        if request.user_agent.browser == "msie":
            return render_template( 'ie.html' )
    if not (request.args.has_key('hitId') and request.args.has_key('assignmentId')):
        raise ExperimentError('hit_assign_worker_id_not_set_in_mturk')
    # Person has accepted the HIT, entering them into the database.
    hitId = request.args['hitId']
    #  Turn assignmentId into unique combination of assignment and worker Id 
    assignmentId = request.args['assignmentId']
    already_in_db = False
    if request.args.has_key('workerId'):
        workerId = request.args['workerId']
        # first check if this workerId has completed the task before (v1)
        nrecords = Participant.query.\
                   filter(Participant.assignmentId != assignmentId).\
                   filter(Participant.workerId == workerId).\
                   count()
        
        if nrecords > 0:
            # already completed task
            already_in_db = True
    else:
        # If worker has not accepted the hit:
        workerId = None
    try:
        part = Participant.query.\
                           filter(Participant.hitId == hitId).\
                           filter(Participant.assignmentId == assignmentId).\
                           filter(Participant.workerId == workerId).\
                           one()                           
        status = part.status
    except:
        status = None
    
    if status == Participant.STARTED:
        # Once participants have finished the instructions, we do not allow
        # them to start the task again.
        raise ExperimentError('already_started_exp_mturk')
    elif status == Participant.COMPLETED:
        # They've done the whole task, but haven't signed the debriefing yet.
        print 'workerId sent to debriefing.html:', workerId
        return render_template('/eg/debriefing.html', 
                               workerId = workerId,
                               assignmentId = assignmentId)
    elif status == Participant.DEBRIEFED:
        # They've done the debriefing but perhaps haven't submitted the HIT yet..
        # Turn asignmentId into original assignment id before sending it back to AMT
        return render_template('/eg/thanks.html', 
                               using_sandbox=USING_SANDBOX, 
                               hitId = hitId, 
                               assignmentId = assignmentId, 
                               workerId = workerId)
    elif already_in_db:
        raise ExperimentError('already_did_exp_hit')
    elif status == Participant.ALLOCATED or status == Participant.CONSENTED or status == Participant.INSTRUCTED or not status:
        # Participant has not yet agreed to the consent. They might not
        # even have accepted the HIT. The mturkindex template will treat
        # them appropriately regardless.
        
        picpath = os.path.normpath(os.path.abspath("pic")+"/img")        
        #ospath = os.pathos.getcwd()
        print "__file_"
        print __file__
        print "ospath"
        print picpath
        return render_template('/eg/mturkindex.html', 
                               hitId = hitId, 
                               assignmentId = assignmentId, 
                               workerId = workerId,
                               ospath = picpath)
    else:
        raise ExperimentError( "STATUS_INCORRECTLY_SET" )


def check_session(user,session):
    print "datetime.now()"
    print datetime.now()
    print "user.lastvisit"
    print user.lastvisit
    print "user.id"
    print user.id
    print "user.sessionId"
    print user.sessionId
    print "session"
    print session
    print "Traceback"
    for line in traceback.format_stack():
        print line.strip()
    if(user.sessionId!=session or not user.lastvisit or (datetime.now() - user.lastvisit) > timedelta (minutes = 10)):         
        return False;
    else:
        user.lastvisit = datetime.now(); # update
        return True;

@app.route('/eg/login', methods=['GET','POST'])
def give_login():
    """
    Serves up the login
    """
    retrivedata()
    
    if(request.method == "POST"):
        if(request.form.has_key('username') and request.form.has_key('pwd') and request.form.has_key('loginsignin')):
            if(request.form['loginsignin']=="new"):
                # Check if username exists in database   
                username = request.form['username'];
                matches = User.query.filter(User.username == username).all();
                if(len(matches)==1):
                    return render_template('/eg/login.html',flag="ALREADY_IN_DB");
                elif(len(matches)==0):
                    user = User();
                    user.username = username;
                    user.password = request.form['pwd'];
                    user.lastvisit = datetime.now();
                    user.sessionId = random.randint(10000000, 99999999);
                    db_session.add(user)
                    db_session.commit()
                    workerId = str(user.id);
                    assignmentId = "0";
                    hitId = "0";
                    return render_template('/eg/consent.html',sessionId=user.sessionId, hitId = hitId, assignmentId=assignmentId, workerId=workerId);
                else:
                    print "Error, user appears in database more than once (serious problem)"
                    raise ExperimentError( 'user_appears_in_database_more_than_once' )            
            elif(request.form['loginsignin']=="returning"):                
                username = request.form['username'];
                password = request.form['pwd'];
                matches = User.query.filter(User.username == username).filter(User.password == password).all();
                if(len(matches)==0):
                    print "no match"
                    return render_template('/eg/login.html',flag="AUTH_FAILED");
                elif(len(matches)==1):
                    user = matches[0];
                    user.lastvisit = datetime.now();
                    user.sessionId = random.randint(10000000, 99999999);
                    db_session.add(user)
                    db_session.commit()
                    workerId = str(user.id);
                    assignmentId = "0";
                    hitId = "0";
                    print "user found"
                    print user.username
                    return render_template('/eg/consent.html',sessionId=user.sessionId, hitId = hitId, assignmentId=assignmentId, workerId=workerId);
                else:
                    print "Error, user appears in database more than once (serious problem)"
                    raise ExperimentError( 'user_appears_in_database_more_than_once' ) 
        else:
            return render_template('/eg/login.html',flag="MISSING_USERNAME_OR_PWD");
    if(request.args.has_key('flag')):
        flag = request.args['flag'];
    else:
        flag = "";        
    return render_template('/eg/login.html',flag=flag)


def check_identity(request):
    if not (request.args.has_key('hitId') and request.args.has_key('assignmentId') and request.args.has_key('workerId')):
        raise ExperimentError('hit_assign_worker_id_not_set')
    hitId = request.args['hitId']
    assignmentId = request.args['assignmentId']
    workerId = request.args['workerId']
    print hitId, assignmentId, workerId
    
    to_return = None;
    
    if not request.args.has_key('sessionId'):
        raise  ExperimentError('sessionId_not_set')
    matches = User.query.filter(User.id == int(workerId)).all();
    if(len(matches)==0):
        to_return = render_template('/eg/login.html',flag="SESSION_EXPIRED");                       
        return [hitId,assignmentId,workerId,None,to_return]
    elif(len(matches)>1):
        print "User in db more than once, serious trouble"
        raise  ExperimentError('user_in_db_more_than_once')
    user = matches[0];
    session = request.args['sessionId'];
    if(not check_session(user,session)):
        to_return = render_template('/eg/login.html',flag="SESSION_EXPIRED");        
    return [hitId,assignmentId,workerId,user,to_return]

@app.route('/eg/consent', methods=['GET','POST'])
def give_consent():
    """
    Serves up the consent in the popup window.
    """
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
    #print res
    return res




def findParticipant(hitId,assignmentId,workerId,addIfNotFound):
    matches = Participant.query.\
                        filter(Participant.hitId == hitId).\
                        filter(Participant.assignmentId == assignmentId).\
                        filter(Participant.workerId == workerId).\
                        all()
    numrecs = len(matches)
    if numrecs == 0:
        print 'Participant not in database yet'
        if(addIfNotFound):
            # Choose condition and counterbalance
            #subj_cond, subj_counter = get_random_condcount()
            
            if not request.remote_addr:
                myip = "UKNOWNIP"
            else:
                myip = request.remote_addr
            
            # set condition here and insert into database
            part = Participant( hitId, myip, assignmentId, workerId, 0, 0)
            part.status = Participant.INSTRUCTED
            db_session.add( part )
            db_session.commit()
            print 'Participant added in database'
            return part
        else:
            return False
    elif numrecs == 1:
        return matches[0]
    else:
        print "Error, hit/assignment appears in database more than once (serious problem)"
        raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )

def findUser(workerId):
    matches = User.query.\
                        filter(User.id == int(workerId)).all()
    numrecs = len(matches)
    if numrecs == 0:
        print 'User not in database yet'
        return False
    elif numrecs == 1:
        return matches[0]
    else:
        print "Error, hit/assignment appears in database more than once (serious problem)"
        raise ExperimentError( 'hit_assign_appears_in_database_more_than_once' )

def redirect(user,hitId,assignmentId,workerId,sessionId):
    if(not user or user.status == User.ALLOCATED):
        return render_template('/eg/consent.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId)
    elif(user.status == User.CONSENTED):
        return render_template('/eg/instruct.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId)
    elif(user.status == User.INSTRUCTED):
        return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=sessionId) 
    else:
        print "Error in redirection"
        raise ExperimentError('user_already_in_game');       

@app.route('/eg/instruct', methods=['GET','POST'])
def give_instruct():
    """
    Serves up the consent in the popup window.
    """
    
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        print "returning to login"
        return to_return
    
    print hitId, assignmentId, workerId

    if(request.method == "POST" and request.form.has_key('instructed') and request.form['instructed']):
        user.status = User.INSTRUCTED
        db_session.add(user)
        db_session.commit()
    
    return redirect(user,hitId,assignmentId,workerId,user.sessionId)

@app.route('/eg/exp', methods=['GET'])
def start_exp():
    """
    Serves up the experiment applet.
    """
    if not (request.args.has_key('hitId') and request.args.has_key('assignmentId') and request.args.has_key('workerId')):
        raise ExperimentError( 'hit_assign_worker_id_not_set_in_exp' )
    hitId = request.args['hitId']
    assignmentId = request.args['assignmentId']
    workerId = request.args['workerId']
    print hitId, assignmentId, workerId
    
    
    # check first to see if this hitId or assignmentId exists.  if so check to see if inExp is set
    matches = Participant.query.\
                        filter(Participant.hitId == hitId).\
                        filter(Participant.assignmentId == assignmentId).\
                        filter(Participant.workerId == workerId).\
                        all()
    numrecs = len(matches)
    if numrecs == 0:
        # Choose condition and counterbalance
        #subj_cond, subj_counter = get_random_condcount()
        
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
    
    return render_template('/eg/exp.html', workerId=part.workerId, assignmentId=part.assignmentId, cond=part.cond, counter=part.counterbalance )


@app.route('/eg/waitingroom', methods=['GET','POST'])
def wait_in_room():
    """
    Serves up the waiting message in the popup window.
    """
     
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        print "returning to login"
        return to_return      
    print hitId, assignmentId, workerId
    
    if(user.status<=User.ALLOCATED):
        if (request.args.has_key('getFlag')):
            return -2
        else:
            # Participant needs to consent and get the game instructions first
            return render_template('/eg/consent.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId = user.sessionId)     
    

    if(user.status<=User.CONSENTED):
        if (request.args.has_key('getFlag')):
            return -3
        else:            
            return render_template('/eg/instruct.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId = user.sessionId)    
    
    
    print "Annoying query"
    currentGamesets = GameSet.query.join(Participant.gamesets)\
                            .filter(Participant.workerId == str(user.id))\
                            .filter(GameSet.status!=GameSet.TERMINATED).all()
    print "Annoying query end"
    print "len(currentGamesets)"
    print len(currentGamesets)
    if len(currentGamesets)== 0:
        # assign a gameset to the participant        
        vacantGameSets = db_session.query(GameSet.id,func.count(GameSet.id),GameSet.numExpectedParticipants,Participant.workerId,Participant.assignmentId).\
                join((Participant,GameSet.participants)).\
                group_by(GameSet.id).\
                having(func.count(GameSet.id)<GameSet.numExpectedParticipants)
        
        print 'Number of vacant games:'
        print vacantGameSets.all()
        print vacantGameSets.count()
        if(vacantGameSets.count()==0):
            gameset = GameSet();
            gameset.numExpectedParticipants = 3;
            db_session.add( gameset )
            db_session.commit()
            
            #creation of the part : link between user and gameset
            addIfNotFound = True # added in consent only
            part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)
            
            part.gamesets.append(gameset);            
            
            game = Game();
            game.num = 1;
            game.numExpectedParticipants = gameset.numExpectedParticipants;            
            gameset.games.append(game);
            part.games.append(game);
            db_session.add( game )
            db_session.commit()
            hidId = str(gameset.id);
            assignmentId = str(gameset.id);            
            part.hitId = hidId;
            part.assignmentId = assignmentId;
            db_session.commit()
        else:
            gamesetTuple = vacantGameSets.order_by(func.count('*').desc()).first()
            gameset = db_session.query(GameSet).get(gamesetTuple[0])
            print 'gameset.id:'
            print gameset.id
            
            #retrival of the part : link between user and gameset
            addIfNotFound = True # added in consent only
            part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)            
            if(not part):
                print "Participant not found in waiting room even though gameset exists"
                raise('participant_not_found_gameset_exists_waiting_room')
            part.gamesets.append(gameset)            
            game = db_session.query(Game).filter(Game.num==1).join(GameSet.games).filter(Game.gamesetid == gameset.id).one(); 
            part.games.append(game)
            print 'Vacant games:'
            for item in vacantGameSets.all():
                print item
            print gamesetTuple
            for item in gamesetTuple:
                print item
            #part.gamesets.append(gameset);
            #part.games.append(game);            
            db_session.commit()
            #hidId = str(gameset.id);
            #assignmentId = str(gameset.id);
            #part.hitId = hidId;
            #part.assignmentId = assignmentId;
            #db_session.commit()
            
    elif (len(currentGamesets)== 1):
        gameset = currentGamesets[0];
        #retrival of the part : link between user and gameset
        addIfNotFound = False # added in consent only
        part = findParticipant(str(gameset.id),str(gameset.id),str(user.id),addIfNotFound)
        if(not part):
            print "Participant not found in waiting room even though gameset exists"
            raise('participant_not_found_gameset_exists_waiting_room')
    else:
        print "Error, participant has started more than one game at the same time"
        raise ExperimentError( 'part_has_more_than_one_started_game' )
                
    numParticipants = len(gameset.participants);
    print 'Num participants :'
    print numParticipants
    
    print "The part"
    print "workerId"
    print part.workerId
    workerId = part.workerId
    print "assignmentId"
    print part.assignmentId
    assignmentId = part.assignmentId
    print "hitId"
    print part.hitId
    hitId = part.hitId
    print "sessionId"
    print user.sessionId
    sessionId = user.sessionId
    
    if(gameset.numExpectedParticipants > numParticipants):
        if (request.args.has_key('getFlag')):
            return str(gameset.numExpectedParticipants - numParticipants)
        else:
            return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, sessionId=sessionId, workerId=workerId, missingParticipant=str(gameset.numExpectedParticipants - numParticipants))
    elif(gameset.numExpectedParticipants == numParticipants):
        if (request.args.has_key('getFlag')):
            return "-1"
        else:
            return start_exp_consensus(part)
    else:
        raise ExperimentError( 'to_many_participants' )
                
@app.route('/eg/intermediatepage', methods=['GET'])
def intermediate():
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, sessionId=user.sessionId)
            

@app.route('/eg/expconsensus', methods=['GET','POST'])
def start_exp_consensus(part = None):
    """
    Serves up the experiment applet.
    """    
    
    # check first to see if this hitId or assignmentId exists.  if so check to see if inExp is set
    
    if(part==None):
        [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
        if to_return!=None:
            print "returning to login"
            return to_return
        print hitId, assignmentId, workerId
        print "starting experiment consensus"
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
            #if not request.remote_addr:
            #    myip = "UKNOWNIP"
            #else:
            #    myip = request.remote_addr
        else:
            part = matches[0]            
    else:
        print "Participant given as paramter"
        hitId, assignmentId, workerId = part.hitId, part.assignmentId, part.workerId;
        user = User.query.filter(User.id==int(workerId)).one(); 
    
    #if part.status>=Participant.STARTED: # in experiment (or later) can't restart at this point
    #    pass
        #raise ExperimentError( 'already_started_exp' )
    #else:
    print "len(part.gamesets)"
    print len(part.gamesets)
    if(len(part.gamesets)==0):
        print "Going back to waiting room"
        return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId)
    gameset = part.gamesets[0];
    curgame = db_session.query(Game).join(GameSet).filter(Game.gamesetid==gameset.id).filter(gameset.curGameNum()==Game.num).one()            
    numParticipants = len(gameset.participants);
    if(gameset.numExpectedParticipants > numParticipants):
        # Preventing trouble
        return render_template('/eg/waitingroom.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId, missingChoices=str(gameset.numExpectedParticipants - numParticipants),sessionId=user.sessionId)
    elif(gameset.numExpectedParticipants < numParticipants):
        raise ExperimentError( 'to_many_participants' )
    
    ###
    # Start of the experiment
    ###                        
    # Added by coco
    imageurl = [];                        
    imageurl.append("/static/pic/img"+str(curgame.image[0].pic_name)+".png")
    imageurl.append("/static/pic/img"+str(curgame.image[1].pic_name)+".png")
    imageurl.append("/static/pic/img"+str(curgame.image[2].pic_name)+".png")            
    question = []
    question.append("What is the percentage of "+curgame.image[0].color+" in the image ?")
    question.append("What is the percentage of "+curgame.image[1].color+" in the image ?")
    question.append("What is the percentage of "+curgame.image[2].color+" in the image ?")            
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
                              'color' : color
                              }
    print "Attributes :"
    print expconsensusAttributes["question"]
    print expconsensusAttributes["question"][0]
    
    print "Content in form"
    for item in request.form:
        print item        
    if(len(request.form)>0 and not request.form.has_key('No decision')):
        print "Adding a participant new choice"
        # Adding the new choice
        #rounds = curgame.rounds;
        #curround = db_session.query(Round).join(Choice).filter(Choice.roundid==Round.id and Choice.workerId == part.workerId and Choice.assignmentId == part.assignmentId).join(Game).filter(Round.gameid==curgame.id).filter(gameset.curGameNum()==Game.num).one()
                        
        curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curgame.curRoundNum()==Round.num).one()
        
        expconsensusAttributes['round']=curgame.curRoundNum();
        if(not isChoiceMade(curround,part) and curround.num == int(request.form['roundNum'])):
            decision0 = Decision()
            decision1 = Decision()
            decision2 = Decision()
            decision0.num = 0
            decision1.num = 1
            decision2.num = 2
            decision0.value = request.form['decision0']
            decision1.value = request.form['decision1']
            decision2.value = request.form['decision2']
            print "The auto status"
            print request.form['auto']
            choiceStatus = Decision.USER_MADE;
            if(int(request.form['auto'])==1):
                print "Found auto status"
                choiceStatus = Decision.AUTO;
            print "The choice status"
            print choiceStatus
            decision0.status = choiceStatus
            decision1.status = choiceStatus
            decision2.status = choiceStatus
            
            print "Decision and percent"
            print decision0.value
            print float(decision0.value)
            print curround.game.image[0].percent
            errorsize0 = abs(float(decision0.value) - curround.game.image[0].percent);
            errorsize1 = abs(float(decision1.value) - curround.game.image[1].percent);
            errorsize2 = abs(float(decision2.value) - curround.game.image[2].percent);                                                            
            decision0.reward = reward(errorsize0,curround.maxreward);                            
            decision1.reward = reward(errorsize1,curround.maxreward);
            decision2.reward = reward(errorsize2,curround.maxreward);
                                 
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
            expconsensusAttributes['status'] = "CHOICE_MADE"
            missingChoices = len(curgame.participants)-len(curround.choices)                    
            expconsensusAttributes['missingChoices'] = str(missingChoices);
            
            if(missingChoices==0):
                print "Round "+str(curround.num)+" is over"
                curround.status=Round.TERMINATED;
                if(curround.num==curgame.numRounds):
                    print "Game is over"
                    curgame.status = Game.TERMINATED;
                    if(gameset.curGameNum()==gameset.numGames):                            
                        print "Game set is over"
                        expconsensusAttributes['status'] = "GAMESET_OVER"
                        gameset.status = GameSet.TERMINATED;
                        curgame.status = Game.TERMINATED;
                    else:
                        expconsensusAttributes['status'] = "GAME_OVER"
                        curgame.status = Game.TERMINATED;
                        newgame = Game();
                        newgame.num = curgame.num+1;
                        newgame.numExpectedParticipants = gameset.numExpectedParticipants;                                
                        gameset.games.append(newgame);
                        for thepart in gameset.participants:
                            thepart.games.append(newgame);
                        db_session.commit()    
                            
                    
                else:
                    # Starting a new round
                    print "Starting a new round"                                                                        
                    curround = Round()
                    curround.num = curgame.curRoundNum()+1
                    print "Starting round "+ str(curround.num)
                    if((curgame.num==1 and curround.num<=3) or (curgame.num>1 and curround.num==1)):
                        curround.type = Round.LONE;
                        curround.maxreward = 5;
                    else:
                        curround.type = Round.SOCIAL; 
                        curround.maxreward = 10;                               
                    curround.status = Round.STARTED
                    curround.startTime = datetime.now()
                    curgame.rounds.append(curround)
                    db_session.commit()

            # Redirect to an intermediate page to avoid double posting
            return render_template('/eg/intermediatepage.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId)
        else:
            print "Decision but no choice made"
            if(curround.num != int(request.form['roundNum'])):
                print "Problem : posting probably from old round to current round"
                print "This may be due to server lag"
                print "Aborting decision making"
                print "curround.num"
                print curround.num  
                print "request.form['roundNum']"
                print request.form['roundNum']                                                                                                                                                                                  
    else:
        print "No decision"
                                    
    print "Sending round info"
    
    if(curgame.curRoundNum()==0):
        # Setting the first round
        print "Setting the first round"
        curround = Round();
        curround.num = 1;
        curround.type = Round.LONE;
        curround.maxreward = 5;                            
        curround.status = Round.STARTED
        curround.startTime = datetime.now()
        curgame.rounds.append(curround)                                                                    
        db_session.commit()
                
    curround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(curgame.curRoundNum()==Round.num).one()                                                            
#            if(curround.status != Round.STARTED):
#                if(curround.status == Round.TERMINATED and (expconsensusAttributes["status"]=="GAME_OVER" or expconsensusAttributes["status"]=="GAMESET_OVER")):
#                    pass                    
#                else:
#                    print "Error, current round should be started"
#                    raise ExperimentError( 'current_round_in_wrong_status' )
#            else:
    print "Round "+ str(curgame.curRoundNum())
    expconsensusAttributes['round']=curgame.curRoundNum();
    
    if(curgame.curRoundNum()>1):
        # Past estimation to display                                            
        prevround = db_session.query(Round).join(Game).filter(Round.gameid==curgame.id).filter(Round.num==curgame.curRoundNum()-1).one()
        prevchoice = db_session.query(Choice).filter(Choice.workerId == workerId and Choice.assignmentId == assignmentId).join(Round).join(Game).filter(Round.gameid==curgame.id).filter(Round.num==curgame.curRoundNum()-1).one()
        listprevround = prevround.listOfChoices()
        listprevchoice = prevchoice.listOfDecisions()
        print "listprevround"
        print listprevround
        listprevround = json.dumps(listprevround)
        print "listprevround json form"  
        print listprevround                                                                                          
        expconsensusAttributes['prevRoundHTML']=listprevround;
        expconsensusAttributes['prevChoice']=listprevchoice;
                                        
    if(isChoiceMade(curround,part)):
        expconsensusAttributes['status'] = "CHOICE_MADE"
        missingChoices = len(curgame.participants)-len(curround.choices)
        expconsensusAttributes['missingChoices'] = str(len(curgame.participants)-len(curround.choices));
        if(missingChoices==0 and curround.num == curgame.numRounds):
            print "Game over in the wrong way"
            
            if(gameset.curGameNum()==gameset.numGames):                            
                print "Game set is over"
                expconsensusAttributes['status'] = "GAMESET_OVER"
                gameset.status = GameSet.TERMINATED;
                curgame.status = Game.TERMINATED;
                db_session.commit()
            else:
                expconsensusAttributes['status'] = "GAME_OVER"
                curgame.status = Game.TERMINATED;
                newgame = Game();
                newgame.num = curgame.num+1;
                newgame.numExpectedParticipants = gameset.numExpectedParticipants;                                
                gameset.games.append(newgame);
                for thepart in gameset.participants:
                    thepart.games.append(newgame);
                db_session.commit()                                                            
    else:
        expconsensusAttributes['status'] = "CHOICE_TO_BE_MADE"            
    remainingTime = timedelta(0,100) + curround.startTime - datetime.now()
    print "remainingTime now"
    print remainingTime.seconds
    expconsensusAttributes['remainingTime'] = remainingTime.seconds
    if(curround.type==Round.LONE):
        expconsensusAttributes['roundType'] = "LONE";                
    else:
        expconsensusAttributes['roundType'] = "SOCIAL";
    expconsensusAttributes['reward'] = curround.maxreward;
    if (request.args.has_key('getFlag')):
        print "In Update"
        print json.dumps(expconsensusAttributes)
        return json.dumps(expconsensusAttributes)
    else:
        print "Not In Update"
        expconsensusAttributes['sessionId']=user.sessionId
        return render_template('/eg/expconsensus.html', **expconsensusAttributes)                                                                                                                                                                            


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
    print "/inexp"
    if not request.form.has_key('assignmentId'):
        print "No assignmentId in inexp route enterexp"
        raise ExperimentError('improper_inputs')
    assignmentId = request.form['assignmentId']
    user = Participant.query.\
            filter(Participant.assignmentId == assignmentId).\
            one()
    print "The participant is starting"
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
    return render_template('/eg/error.html', errornum= experiment_errors['intermediate_save'])

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

@app.route('/eg/questionnaire', methods=['POST', 'GET'])
def questionnaire():
    """
    User has finished the experiment and is posting their data in the form of a
    (long) string. They will receive a debreifing back.
    """
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    
    print "In questionnaire"    
    print "assignmentId"
    print assignmentId
    print "workerId"    
    print workerId        
    print "hitId"    
    print hitId    
    print "user.sessionId"
    print user.sessionId
    
    try:
        part = Participant.query.\
                filter(Participant.assignmentId == assignmentId).\
                filter(Participant.workerId == workerId).\
                one()
    except:
        raise ExperimentError('improper_inputs')
    
    if request.method == 'GET':
        print "Questionnaire : In POST"
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
        db_session.commit();      
        questionnaireHTML = {"workerId": workerId,
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
        "sympathetic":questionnaire.sympathetic}
        
        
        
        if(request.args.has_key('getFlag')):            
            return render_template('/eg/questionnaire.html', **questionnaireHTML)
        else:
            return render_template('/eg/questionnaire.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId)
    if request.method == 'POST':
        print "Questionnaire : In POST"
        questionnaire = Questionnaire.query.filter(Questionnaire.userid == int(workerId)).filter(Questionnaire.gamesetid== int(hitId)).one()
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
        questionnaire.aloneAnswer = request.form['alone']=="yes"
        questionnaire.communicate = request.form['communicate']=="yes"
        #questionnaire.communicateDescription = request.form['communicateDescription']
        db_session.commit()
        return render_template('/eg/debriefing.html', hitId = hitId, assignmentId=assignmentId, workerId=workerId,sessionId=user.sessionId)
    


@app.route('/eg/debriefing', methods=['POST', 'GET'])
def savedata():
    """
    User has finished the experiment and is posting their data in the form of a
    (long) string. They will receive a debreifing back.
    """
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    print assignmentId #, datastring
    
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
            total = total + decision.reward;
                 
    part.status = Participant.COMPLETED    
    #user.datastring = datastring
    user.endhit = datetime.now()
    db_session.add(user)
    db_session.commit()
    
    return render_template('/eg/debriefing.html', hitId = hitId, workerId=workerId, assignmentId=assignmentId,sessionId=user.sessionId, totalreward=total)

@app.route('/eg/complete', methods=['POST'])
def completed():
    """
    This is sent in when the participant completes the debriefing. The
    participant can accept the debriefing or declare that they were not
    adequately debriefed, and that response is logged in the database.
    """
    print "accessing the /complete route"
    [hitId,assignmentId,workerId,user,to_return] = check_identity(request);
    if to_return!=None:
        return to_return;
    agreed = request.form['agree']
    print workerId, assignmentId, agreed
    
    part = Participant.query.\
            filter(Participant.assignmentId == assignmentId).\
            filter(Participant.workerId == workerId).\
            one()
    part.status = Participant.DEBRIEFED
    part.debriefed = agreed == 'true'
    db_session.add(part)
    db_session.commit()
    return render_template('/eg/login.html')
    #return render_template('/eg/closepopup.html')

#------------------------------------------------------
# routes for displaying the database/editing it in html
#------------------------------------------------------
@app.route('/eg/list')
@requires_auth
def viewdata():
    """
    Gives a page providing a readout of the database. Requires password
    authentication.
    """
    people = Participant.query.\
              order_by(Participant.assignmentId).\
              all()
    print people
    people = get_people(people)
    return render_template('/eg/simplelist.html', records=people)

@app.route('/eg/updatestatus', methods=['POST'])
@app.route('/eg/updatestatus/', methods=['POST'])
def updatestatus():
    """
    Allows subject status to be updated from the web interface.
    """
    if request.method == 'POST':
        field = request.form['id']
        value = request.form['value']
        print field, value
        [tmp, field, assignmentId] = field.split('_')
        
        user = Participant.query.\
                filter(Participant.assignmentId == assignmentId).\
                one()
        if field=='status':
            user.status = value
        db_session.add(user)
        db_session.commit()
        
        return value

@app.route('/eg/dumpdata')
@requires_auth
def dumpdata():
    """
    Dumps all the data strings concatenated. Requires password authentication.
    """
    ret = '\n'.join([subj.datastring for subj in Participant.query.all()])
    response = make_response( ret )
    response.headers['Content-Disposition'] = 'attachment;filename=data.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

# @app.route("/img<int:pid>.png")
# def getImage(pid):    
#     print "Responding to image request"    
#     print pid
#     imgname = "img"+str(pid)+".png"
#     imgpath = os.path.normpath(os.path.abspath("pic/"+imgname))
#     print imgname
#     print imgpath
#     img = open(imgpath,'r')
#     print "end2"
#     response = make_response(img)
#     response.headers['Content-Type'] = 'image/png'
#     response.headers['Content-Disposition'] = 'attachment; filename='+'"'+imgname+'"'
#     #print response
#     print "end3"
#     return response

#----------------------------------------------
# generic route
#----------------------------------------------
@app.route('/eg/<pagename>')
def regularpage(pagename=None):
    """
    Route not found by the other routes above. May point to a static template.
    """
    if pagename==None:
        raise ExperimentError('page_not_found')
    return render_template(pagename)

#----------------------------------------------
# functions added by sam - June 2013
#----------------------------------------------

def link_participant_to_game(user):
    currentWaitingGames = Game.query.filter(Game.status == Game.WAITING_FOR_PARTICIPANTS);
    if(user.game != None):
        print "user is already in a game"
        raise ExperimentError('user_already_in_game');
    elif(currentWaitingGames.count()>0):
        game = currentWaitingGames.one();
    else: 
        game = Game();
        db_session.add(game);
    

    game.participants.append(user);
    if(game.participants.count()==game.numExpectedParticipants):
        game.status = game.STARTED;
    user.games.append(game);
    db_session.commit();
    return game







    








#############################    
    
#@app.route('/eg/')
#def hello_world():
#    return 'Hello World!'
#	
#@app.route('/eg/getdbinfo')
#def get_db_info():
#	#return "in db info"
#	try:
#		#services = json.loads(os.getenv("VCAP_SERVICES", "{}"))	
#		services = os.getenv("VCAP_SERVICES", "{}")
#		if services:
#			return services
#		else:
#			return "no services"
#	except:
#		return "exception"	


def retrivedata():
    print "Start data retrival"
    #vacantGameSets = db_session.query(GameSet.id,func.count(GameSet.id),GameSet.numExpectedParticipants,Participant.workerId,Participant.assignmentId).\
    #            join((Participant,GameSet.participants)).\
    #            group_by(GameSet.id).\
    #            having(func.count(GameSet.id)<GameSet.numExpectedParticipants)
                
#    data = db_session.query(GameSet.id,Participant.assignmentId,Game.id,Decision.num,Image.percent,Round.id,Participant.workerId,Decision.value).\
#                join(Participant.gamesets).\
#                filter(Game.gamesetid==GameSet.id).\
#                filter(Round.gameid==Game.id).\
#                filter(Choice.roundid==Round.id).\
#                filter(Decision.choiceid==Choice.id).\
#                filter(Image.gameid==Game.id).order_by(GameSet.id,Participant.assignmentId,Game.id,Decision.num,Round.id,Participant.workerId,Decision.value).all()#  ,Image.percent
    sql_request = sqlalchemy.text('\
    SELECT\
    gamesets.id AS gamesets_id,\
    games.id AS games_id,\
    decisions.num AS decisions_num,\
    rounds.id AS rounds_id, \
    participants.`workerId` AS `participants_workerId`,\
    decisions.value AS decisions_value \
    FROM \
    (gamesets\
    INNER JOIN gamesets_participants ON gamesets_participants.gamesetid = gamesets.id\
    INNER JOIN participants ON participants.assignmentId = gamesets_participants.assignmentId AND participants.workerId =\
gamesets_participants.workerId \
    INNER JOIN games ON games.gamesetid = gamesets.id\
    INNER JOIN rounds ON rounds.gameid = games.id\
    INNER JOIN choices ON choices.roundid = rounds.id and choices.workerId = participants.workerId and choices.assignmentId\
= participants.assignmentId\
    INNER JOIN decisions ON decisions.choiceid = choices.id)\
    ORDER BY gamesets.id, participants.`assignmentId`, games.id, decisions.num, rounds.id, participants.`workerId`, decisions.value\
    ')
    data = engine.execute(sql_request).fetchall()
    print "Data"
    print data
    for item in data:
        print item
    print "data length"
    print len(data)
        
###########################################################
# let's start
###########################################################

# Initialize database if necessary
init_db()
		
if __name__ == '__main__':
    #sys.stdout = open('mystd.txt', 'w')
    #print site.getsitepackages()
    print(get_python_lib())
    print os.path.abspath(os.path.dirname(__file__))
    
    retrivedata()
    
    
