<?php
//********************************** 
$hostname = "localhost";
$database = "eg_test";
$username = "root";
$password = "root";
$db_connection= mysql_connect($hostname, $username, $password) or trigger_error(mysql_error(),E_USER_ERROR); 

	/*function create_tables($database)
{	$tables=array('user'=>
										'(userid varchar(5) PRIMARY KEY,
											username  varchar(50) NOT NULL,
											password varchar(50),
											lastvisit varchar(50),
											sessionid varchar(100),
											userstatuscode varchar(2),
											datastring text)
											email varchar(100),
											ipaddress = varchar(20),
											note text)',
										 worker = relationship("Participant",backref="user",cascade="all,delete")
											codes = relationship("Code",backref="user",cascade="all,delete")', 
									'userstatus'=>
											'(userstatuscode varchar(2) PRIMARY KEY,
																 userstatuslibcode varchar(20))',
									'image'=>
											'(imageid varchar(5) PRIMARY KEY, 
												pic_name varchar(100),
											percent = Column(Integer, nullable=True)   
											complexity = Column(Integer, nullable=True) 
											color = Column(String(128),nullable=True)
											status = Column(Integer, default=FREE)
											gameid = Column(Integer, ForeignKey(TABLE_GAME+'.id',
																													 use_alter=True, name='fk_image_game_id',
																													 onupdate="CASCADE", ondelete="CASCADE"))
											'
    FREE = 1
    USED = 2

    
									
									
    
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

Index('idx_assignment_worker_gameset', gameset_participant_table.c.assignmentId, gameset_participant_table.c.workerId),

keycode_gameset_user = Table(TABLE_KEYCODE_GAMESET_USER, Base.metadata,
    Column('keyCodeBegin', String(128), nullable=False, primary_key=True),
    Column('userId', Integer, nullable=False,default=-1),
    Column('gamesetid', Integer, nullable=False, default= -1),
    Column('keyCodeEnd', String(128), nullable=False,default='')
),

image_game = Table(TABLE_IMAGE, Base.metadata,
    Column('imageid', Integer, nullable=False),
    Column('gameid', Integer, nullable=False)
),

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

Index('idx_assignment_worker', game_participant_table.c.assignmentId, game_participant_table.c.workerId),


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
        print "TABLE_PARTICIPANT"
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
    numGames = Column(Integer, default = 10);
    datastring = Column(Text, nullable=True)
    startTime = Column(DateTime, nullable=True)
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
            self.datastring )
    
    def curGameNum(self):
        return(len(self.games))

# Added by coco

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
    # Added by coco
    image = relationship("Image",backref="game",cascade="all,delete")
    
    # many to many Game<->Participant
    #participants = relationship('Participant', secondary=Games_Participants, backref='games')

    # one to many Game<->Round
    rounds = relationship("Round",backref="game",cascade="all,delete")
    
    def __init__(self):
        # Added by coco: create 3 pictures
	# WARNING : to be modified to fetch 3 FREE images from the database
        

        matches = Image.query.filter(Image.status == Image.FREE).all()
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
                            
Index('idx_game_in_round', Round.gameid)

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


Index('idx_round_in_choice', Choice.roundid)
Index('idx_assignment_worker_in_choice', Choice.assignmentId, Choice.workerId)

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
    
    def __init__(self):
        pass

    
    def __repr__( self ):
        return "Subject(%s, %r, %r, %s)" % ( 
            self.id,             
            self.status,
            self.datastring )

Index('idx_choice_in_decision', Decision.choiceid)


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

Index('idx_user_in_code', Code.userid)


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
    aloneAnswer = Column(Boolean, default=True)
    #aloneQuestion = "Have you completed the game alone ?"
    communicate = Column(Boolean, default=True)
    #communicateQuestion = "Have you communicated with the other participant in any way druing the game ?"
    communicateDescription = Column(Text, default="")
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

Index('idx_user_in_questionnaire', Questionnaire.userid)
	foreach(array('01'=>'ALLOCATED','02'=>'CONSENTED','03'=>'ASSESSED','04'=>'INSTRUCTED') as $userstatuscode=>$userstatuslibcode)
	{ $updateSQL="insert into userstatus values (".GetSQLValueString($userstatuscode, "text").",".GetSQLValueString($userstatuslibcode, "text").")";
		mysql_query($updateSQL);
	}
}*/
/*class User(Base):
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

class Image(Base):
    """
    Object representation of a decision in the database.
    """
    __tablename__ = TABLE_IMAGE
    
    FREE = 1
    USED = 2

    id = Column(Integer, primary_key=True) 
    pic_name = Column(String(128), nullable=True)
    percent = Column(Integer, nullable=True)   
    complexity = Column(Integer, nullable=True) 
    color = Column(String(128),nullable=True)
    status = Column(Integer, default=FREE)
    gameid = Column(Integer, ForeignKey(TABLE_GAME+'.id',
                                         use_alter=True, name='fk_image_game_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))
    
    def __init__(self, pic_name, percent,color,complexity):
        self.pic_name = pic_name
        self.percent = percent
        self.color = color
        self.complexity = complexity

    
    def __repr__( self ):
        return "Subject(%s, %r, %r, %s)" % ( 
            self.id,             
            self.status,
            self.datastring )

#Index('idx_game_in_image', Image.gameid),
*/
?>
