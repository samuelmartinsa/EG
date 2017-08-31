
import datetime
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.types import REAL
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import and_
from db import Base
from sqlalchemy.schema import ForeignKeyConstraint, Index, UniqueConstraint
from config import config
from db import db_session, init_db

# Add by coco
#from picgencol import picgencol
from fractale_new import fractale_new
import random
# added by sam
#TABLENAME = config.get('Database Parameters', 'table_name')
TABLE_GAME = config.get('Database Parameters', 'table_game')
TABLE_GAMESET = config.get('Database Parameters', 'table_gameset')
TABLE_PARTICIPANT = config.get('Database Parameters', 'table_participant')
TABLE_USER = config.get('Database Parameters', 'table_user')
TABLE_GAME_PARTICIPANT = config.get('Database Parameters', 'table_game_participant')
TABLE_GAMESET_PARTICIPANT = config.get('Database Parameters', 'table_gameset_participant')
TABLE_ROUND = config.get('Database Parameters', 'table_round')
TABLE_CHOICE = config.get('Database Parameters', 'table_choice')
TABLE_DECISION = config.get('Database Parameters', 'table_decision')
TABLE_QUESTIONNAIRE = config.get('Database Parameters', 'table_questionnaire')
TABLE_CODE = config.get('Database Parameters', 'table_code')
TABLE_IMAGE = config.get('Database Parameters', 'table_image') # Added by coco
CODE_VERSION = config.get('Task Parameters', 'code_version')
TABLE_KEYCODE_GAMESET_USER=config.get('Database Parameters', 'table_keycode_gameset_user')
TABLE_PARTICIPANT_STATUS=config.get('Database Parameters', 'table_participant_status')
#TABLE_IMAGE_GAME=config.get('Database Parameters', 'table_image_game')
# association tables

gameset_participant_table = Table(TABLE_GAMESET_PARTICIPANT, Base.metadata,
    Column('gamesetid', Integer, ForeignKey(TABLE_GAMESET+'.id',
                                          use_alter=True, name='fk_gameset_part_game_id')),
    Column('assignmentId', String(128), nullable=False),
    Column('workerId', String(128), nullable=False) ,
    ForeignKeyConstraint(['assignmentId','workerId'],
                          [TABLE_PARTICIPANT+'.assignmentId',
                           TABLE_PARTICIPANT+'.workerId'],                          
                        use_alter=True, name='fk_gameset_part_part_id',
                        onupdate="CASCADE", ondelete="CASCADE")
)

#Index('idx_assignment_worker_gameset', gameset_participant_table.c.assignmentId, gameset_participant_table.c.workerId),
# status='',IN_USE,USED
keycode_gameset_user = Table(TABLE_KEYCODE_GAMESET_USER, Base.metadata,
    Column('keyCodeBegin', String(128), nullable=False, primary_key=True),
    Column('creationtime', DateTime, nullable=True),
    Column('usagetime', DateTime, nullable=True),
    Column('userid', Integer, nullable=False,default=-1),
    Column('gamesetid', Integer, nullable=False, default= -1),
    Column('keyCodeEnd', String(128), nullable=False,default=''),
    Column('totalreward', REAL, nullable=True),
    Column('status',String(128),nullable=False),
    Column('cwf_contributor_id',String(128),nullable=True,default=''),
    Column('bonus',String(10), nullable=True,default=''),
    Column('paidtime',DateTime, nullable=True),
    Column('resultpaycode',String(128), nullable=True,default=''),
    Column('resultpaymessage', Text, nullable=True)
),

participant_status = Table(TABLE_PARTICIPANT_STATUS, Base.metadata,
    Column('participant_statuscode', Integer, nullable=False, primary_key=True),
    Column('participant_statuslib', String(128), nullable=False)
),

"""image_game = Table(TABLE_IMAGE, Base.metadata,
    Column('imageid', Integer, nullable=False),
    Column('gameid', Integer, nullable=False)
),"""

game_participant_table = Table(TABLE_GAME_PARTICIPANT, Base.metadata,
    Column('gameid', Integer, ForeignKey(TABLE_GAME+'.id',
                                          use_alter=True, name='fk_game_part_game_id')),
    Column('assignmentId', String(128), nullable=False),
    Column('workerId', String(128), nullable=False) ,
    ForeignKeyConstraint(['assignmentId','workerId'],
                          [TABLE_PARTICIPANT+'.assignmentId',
                           TABLE_PARTICIPANT+'.workerId'],                          
                        use_alter=True, name='fk_game_part_part_id',
                        onupdate="CASCADE", ondelete="CASCADE")
)

#Index('idx_assignment_worker', game_participant_table.c.assignmentId, game_participant_table.c.workerId),

class User(Base):
    """
    Object representation of a participant in the database.
    """
    __tablename__ = TABLE_USER
    
    # Status codes
    ALLOCATED = 1
    CONSENTED = 2
    ASSESSED = 3
    INSTRUCTED = 4
    
    id = Column(Integer, primary_key=True)
    username = Column(String(128))
    password = Column(String(128))
    worker = relationship("Participant",backref="user",cascade="all,delete")
    lastvisit = Column(DateTime, nullable=True)
    sessionId = Column(String(128), nullable=True)
    status = Column(Integer, default = 1)
    datastring = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    ipaddress = Column(String(128), nullable=True)
    ip_in_use= Column(String(1), nullable=True)
    note =  Column(Text, nullable=True)
    codes = relationship("Code",backref="user",cascade="all,delete")
    
    def __init__(self):
        pass
    
    def __repr__( self ):
        return "Subject(%s, %s, %r, %r, %s)" % ( 
            self.assignmentId, 
            self.workerId, 
            self.cond, 
            self.status,
            self.codeversion )

#Index('idx_worker_in_user', User.worker)

class Participant(Base):
    """
    Object representation of a participant in the database.
    """
    __tablename__ = TABLE_PARTICIPANT
    
    # Status codes
    ALLOCATED = 1
    CONSENTED = 2
    INSTRUCTED = 3
    STARTED = 4
    COMPLETED = 5
    DEBRIEFED = 6
    CREDITED = 7
    QUITEARLY = 8
    
    assignmentId =Column(String(128), primary_key=True)
    workerId = Column(String(128), primary_key=True)
    hitId = Column(String(128))
    ipaddress = Column(String(128))
    cond = Column(Integer)
    counterbalance = Column(Integer)
    codeversion = Column(String(128))
    beginhit = Column(DateTime, nullable=True)
    beginexp = Column(DateTime, nullable=True)
    endhit = Column(DateTime, nullable=True)
    status = Column(Integer, default = 1)
    debriefed = Column(Boolean)
    datastring = Column(Text, nullable=True)
    
    userid = Column(Integer, ForeignKey(TABLE_USER+'.id',
                                         use_alter=True, name='fk_participant_user_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    
    # many to many Participant<->Game
    games = relationship('Game',
                         secondary=game_participant_table,
                         backref="participants",cascade="all,delete")
    gamesets = relationship('GameSet',
                         secondary=gameset_participant_table,
                         backref="participants",cascade="all,delete")
    choices = relationship("Choice",backref="participant",cascade="all,delete")
        
    def __init__(self, hitId, ipaddress, assignmentId, workerId, cond, counterbalance):
        self.hitId = hitId
        self.ipaddress = ipaddress
        self.assignmentId = assignmentId
        self.workerId = workerId
        self.cond = cond
        self.counterbalance = counterbalance
        self.status = 1
        self.codeversion = CODE_VERSION
        self.debriefed = False
        self.beginhit = datetime.datetime.now()
    
    def __repr__( self ):
        return "Subject(%s, %s, %r, %r, %s)" % ( 
            self.assignmentId, 
            self.workerId, 
            self.cond, 
            self.status,
            self.codeversion )

#Index('idx_user_in_participant', Participant.userid),


# Added by Sam
class GameSet(Base):
    """
    Object representation of a set of games in the database.
    """
    __tablename__ = TABLE_GAMESET
    
    UNUSED = 0
    WAITING_FOR_PARTICIPANTS = 1
    STARTED = 2
    TERMINATED = 3
    
    id = Column(Integer, primary_key=True)
    status = Column(Integer, default = WAITING_FOR_PARTICIPANTS)
    numExpectedParticipants = Column(Integer, default = 2)
    numGames = Column(Integer, default = 10)
    pic_name = Column(Text, nullable=True)
    starttime = Column(DateTime, nullable=True)
    playmode = Column(Text, nullable=True)
    job_id = Column(String(128), nullable=True)
    # many to many Game<->Participant
    #participants = relationship('Participant', secondary=Games_Participants, backref='games')

    # one to many GameSet<->Game
    games = relationship("Game",backref="gameset",cascade="all,delete")
    
    def __init__(self):
      pass
    
    def __repr__( self ):
      return "Subject(%s, %r, %r, %s)" % (
        self.id,
        self.status,
        self.numExpectedParticipants,
        self.numGames,
        self.pic_name )
    
    def curGameNum(self):
      #return(len(self.games))
       curgame=db_session.query(Game.num).filter(Game.status == Game.STARTED).filter(Game.gamesetid == self.id).one()
       return curgame.num
        

# Added by coco
class Image(Base):
    """
    Object representation of a decision in the database.
    """
    __tablename__ = TABLE_IMAGE
    
    #status
    FREE = 1
    USED = 2
    
    
    id = Column(Integer, primary_key=True)
    pic_name = Column(String(128), nullable=True)
    percent = Column(Integer, nullable=True)   
    complexity = Column(Integer, nullable=True) 
    color = Column(String(128),nullable=True)
    pic_type=Column(String(128), nullable=False)
    status = Column(Integer, default=FREE)
    gameid = Column(Integer, ForeignKey(TABLE_GAME+'.id',
                                         use_alter=True, name='fk_image_game_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    
    def __init__(self, pic_name, percent,color,complexity,pic_type):
        self.pic_name = pic_name
        self.percent = percent
        self.color = color
        self.complexity = complexity
        self.pic_type = pic_type
    
    def __repr__( self ):
        return "Subject(%s, %r, %r, %s)" % ( 
            self.id,             
            self.status,
            self.datastring )

#Index('idx_game_in_image', Image.gameid),

class Game(Base):
    """
    Object representation of a game in the database.
    """
    __tablename__ = TABLE_GAME
    
    UNUSED = 0
    WAITING_FOR_PARTICIPANTS = 1
    STARTED = 2
    TERMINATED = 3
    
    id = Column(Integer, primary_key=True)
    num = Column(Integer, default = 1)
    status = Column(Integer, default = WAITING_FOR_PARTICIPANTS)
    numExpectedParticipants = Column(Integer, default = 0)
    numRounds = Column(Integer, default = 3);
    datastring = Column(Text, nullable=True)
    gamesetid = Column(Integer, ForeignKey(TABLE_GAMESET+'.id',
                                         use_alter=True, name='fk_game_gameset_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    image = relationship("Image",backref="game",cascade="all,delete")
    
    # many to many Game<->Participant
    #participants = relationship('Participant', secondary=Games_Participants, backref='games')

    # one to many Game<->Round
    rounds = relationship("Round",backref="game",cascade="all,delete")
    
    def __init__(self,EGParameters):
      # Add 3 pictures to the game
      # matches=images
      # if EGParameters['useExistingGames']=='y':
        # for i in range(0,3):
          # img=Image('nom',0,0,0,'type')
          # db_session.add(img)
          # db_session.commit() 
          # print img.id
          # matches.append(img)
      # else:
      matches = Image.query.filter(Image.status == Image.FREE,Image.pic_type==EGParameters['imageType']).all()
      for curimage in matches[0:3]:
        curimage.status = Image.USED
        self.image.append(curimage)
        db_session.commit() 

    def __repr__( self ):
        return "Subject(%s, %r, %r, %s)" % (
            self.id,
            self.status,
            self.numExpectedParticipants,
            self.numRounds,
            self.datastring )
    
    def curRoundNum(self):
        return(len(self.rounds))


class Round(Base):
    """
    Object representation of a round in the database.
    """
    __tablename__ = TABLE_ROUND
    
    # status
    UNUSED = 0
    STARTED = 1
    TERMINATED = 2
    
    # type
    LONE = 0;
    SOCIAL = 1;
        
    
    id = Column(Integer, primary_key=True)
    num = Column(Integer, default = 1)
    status = Column(Integer, default = 1)
    type = Column(Integer, default = LONE)
    datastring = Column(Text, nullable=True)
    startTime = Column(DateTime, nullable=True)
    endTime = Column(DateTime, nullable=True)
    maxreward = Column(REAL, nullable=True)
    gameid = Column(Integer, ForeignKey(TABLE_GAME+'.id',
                                         use_alter=True, name='fk_round_game_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    choices = relationship("Choice",backref="round",cascade="all,delete")
    
    def __init__(self):
        pass
    
    def __repr__( self ):
        return "Subject(%s, %r, %r, %s)" % ( 
            self.id,
            self.status,
            self.datastring )

    def listOfChoices(self):
        keytuple0 = db_session.query(Decision.value).filter(Decision.num == 0).join(Choice.decisions).filter(Choice.roundid == self.id).join(Round).filter(Round.id == self.id).all()
        keytuple1 = db_session.query(Decision.value).filter(Decision.num == 1).join(Choice.decisions).filter(Choice.roundid == self.id).join(Round).filter(Round.id == self.id).all()
        keytuple2 = db_session.query(Decision.value).filter(Decision.num == 2).join(Choice.decisions).filter(Choice.roundid == self.id).join(Round).filter(Round.id == self.id).all()
        #print "Result from listOfChoices"
        #print keytuple
        res0 = [];
        for item in keytuple0:
            res0.append(item[0])
        res1 = [];
        for item in keytuple1:
            res1.append(item[0])
        
        res2 = [];
        for item in keytuple2:
            res2.append(item[0])
        res = [];
        res.append(res0);    
        res.append(res1);
        res.append(res2);
        #print res
        return res
                            
#Index('idx_game_in_round', Round.gameid)

class Choice(Base):
    """
    Object representation of a choice in the database.
    """
    __tablename__ = TABLE_CHOICE
    
    
    id = Column(Integer, primary_key=True)
    status = Column(Integer, default = 1)
    decisions = relationship("Decision",backref="choice",cascade="all,delete")
    datastring = Column(Text, nullable=True)
    roundid = Column(Integer, ForeignKey(TABLE_ROUND+'.id',
                                         use_alter=True, name='fk_choice_round_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    
    assignmentId =Column(String(128), nullable=False)
    workerId = Column(String(128), nullable=False)
    __table_args__ = (
                    ForeignKeyConstraint(['assignmentId','workerId'],
                          [TABLE_PARTICIPANT+'.assignmentId',
                           TABLE_PARTICIPANT+'.workerId'],name='fk_choice_part_id',
                           onupdate="CASCADE", ondelete="CASCADE"),
                    UniqueConstraint('id')
            )
    
    def __init__(self):
        pass

    
    def __repr__( self ):
        return "Subject(%s, %r, %r, %s)" % ( 
            self.id,             
            self.status,
            self.datastring )
        
    def listOfDecisions(self):
        key0 = db_session.query(Decision.value).filter(Decision.num == 0).join(Choice.decisions).filter(Choice.id == self.id).one()
        key1 = db_session.query(Decision.value).filter(Decision.num == 1).join(Choice.decisions).filter(Choice.id == self.id).one()
        key2 = db_session.query(Decision.value).filter(Decision.num == 2).join(Choice.decisions).filter(Choice.id == self.id).one()
        #print "Result from listOfDecisions"
        #print keytuple
        
        res = [];
        res.append(key0.value);    
        res.append(key1.value);
        res.append(key2.value);
        #print "res Decisions"
        #print res
        return res


#Index('idx_round_in_choice', Choice.roundid)
#Index('idx_assignment_worker_in_choice', Choice.assignmentId, Choice.workerId)

class Decision(Base):
    """
    Object representation of a decision in the database.
    """
    __tablename__ = TABLE_DECISION
    
    USER_MADE = 1;
    AUTO = 2;
    
    id = Column(Integer, primary_key=True)
    status = Column(Integer, default = USER_MADE)    
    num = Column(Integer, nullable=True)
    value = Column(REAL, nullable=True)
    timestamp = Column(String(19), nullable=True) # yyyy-mm-dd-hh-mn-sc
    datastring = Column(Text, nullable=True)
    reward = Column(REAL, nullable=True)
    choiceid = Column(Integer, ForeignKey(TABLE_CHOICE+'.id',
                                         use_alter=True, name='fk_decision_choice_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    imageid = Column(Integer, nullable=True)
    
    def __init__(self):
        pass

    
    def __repr__( self ):
        return "Subject(%s, %r, %r, %s)" % ( 
            self.id,             
            self.status,
            self.datastring )

#Index('idx_choice_in_decision', Decision.choiceid)


class Code(Base):
    """
    Object representation of a user code (CrowdFlower) in the database.
    """
    __tablename__ = TABLE_CODE
    
    FREE = 0;
    USED = 1;
    
    
    id = Column(Integer, primary_key=True)
    status = Column(Integer, default = FREE)    
    num = Column(Integer, nullable=True)
    value = Column(String(128), nullable=True)
    userid = Column(Integer, ForeignKey(TABLE_USER+'.id',
                                         use_alter=True, name='fk_code_user_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    
    def __init__(self):
        pass

    
    def __repr__( self ):
        return "Subject(%s, %r, %r, %s)" % ( 
            self.id,             
            self.status,
            self.datastring )

#Index('idx_user_in_code', Code.userid)


class Questionnaire(Base):
    """
    Object representation of a decision in the database.
    """
    __tablename__ = TABLE_QUESTIONNAIRE
        
    id = Column(Integer, primary_key=True)
    status = Column(Integer, default = 1)    
    userid = Column(Integer, ForeignKey(TABLE_USER+'.id',
                                         use_alter=True, name='fk_questionnaire_user_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    #gamesetid = Column(Integer, ForeignKey(TABLE_GAMESET+'.id',
    #                                     use_alter=True, name='fk_questionnaire_gameset_id',
    #                                     onupdate="CASCADE", ondelete="CASCADE"))
    gamesetid = Column(Integer, default = 0)
    enterQtime= Column(String(19), nullable=True) # yyyy-mm-dd-hh-mn-sc
    leaveQtime= Column(String(19), nullable=True) # yyyy-mm-dd-hh-mn-sc
    #aloneAnswer = Column(Boolean, default=True)
    #aloneQuestion = "Have you completed the game alone ?"
    #communicate = Column(Boolean, default=True)
    #communicateQuestion = "Have you communicated with the other participant in any way druing the game ?"
    #communicateDescription = Column(Text, default="")
    extraverted =  Column(Integer, default=0)
    critical =  Column(Integer, default=0)
    dependable =  Column(Integer, default=0)
    anxious =  Column(Integer, default=0)
    open =  Column(Integer, default=0)
    reserved =  Column(Integer, default=0)
    sympathetic =  Column(Integer, default=0)
    disorganized =  Column(Integer, default=0)
    calm =  Column(Integer, default=0)
    conventional =  Column(Integer, default=0)
    sexe =  Column(Integer, default=0)
    nativespeakenglish =  Column(Integer, default=0)
    schoolgrade =  Column(Integer, default=0)
    def __init__(self):
        pass

    
    def __repr__( self ):
        return "Subject(%r, %r, %r, %r, %r, %r, %s, %r, %r, %r, %r, %r, %r, %r, %r, %r, %r, %r, %r)" % ( 
            self.id,             
            self.status, 
            self.userid,
            self.gamesetid,
            self.aloneAnswer,
            self.communicate,
            self.communicateDescription,
            self.extraverted,
            self.critical,
            self.dependable,
            self.anxious,
            self.open,
            self.reserved,
            self.sympathetic,
            self.disorganized,
            self.calm,
            self.sexe,
            self.nativespeakenglish,
            self.schoolgrade
            )

#Index('idx_user_in_questionnaire', Questionnaire.userid)
#Index('idx_gameset_in_questionnaire', Questionnaire.gamesetid)
