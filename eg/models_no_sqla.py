
from datetime import datetime
from config import config
from db_no_sqla import connection,GetSQLValueString
import MySQLdb

"""gameset_participant_table = Table(TABLE_GAMESET_PARTICIPANT, Base.metadata,
    Column('gamesetid', Integer, ForeignKey(TABLE_GAMESET+'.id',
                                          use_alter=True, name='fk_gameset_part_game_id')),
    Column('assignmentId', String(128), nullable=False),
    Column('workerId', String(128), nullable=False) ,
    ForeignKeyConstraint(['assignmentId','workerId'],
                          [TABLE_PARTICIPANT+'.assignmentId',
                           TABLE_PARTICIPANT+'.workerId'],                          
                        use_alter=True, name='fk_gameset_part_part_id',
                        onupdate="CASCADE", ondelete="CASCADE")
)"""

#Index('idx_assignment_worker_gameset', gameset_participant_table.c.assignmentId, gameset_participant_table.c.workerId),
# status='',IN_USE,USED
"""keycode_gameset_user = Table(TABLE_KEYCODE_GAMESET_USER, Base.metadata,
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
),"""

"""participant_status = Table(TABLE_PARTICIPANT_STATUS, Base.metadata,
    Column('participant_statuscode', Integer, nullable=False, primary_key=True),
    Column('participant_statuslib', String(128), nullable=False)
),"""

"""image_game = Table(TABLE_IMAGE, Base.metadata,
    Column('imageid', Integer, nullable=False),
    Column('gameid', Integer, nullable=False)
),"""

"""game_participant_table = Table(TABLE_GAME_PARTICIPANT, Base.metadata,
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
"""
class Table(object):# old style class => inherits from object
  
  
  def __init__(self, dictionary,action):
    for key in dictionary:
      if hasattr(self, key):
        setattr(self, key, dictionary[key])
    
    if action=='insert':
      self.insert()
    elif action=='update':
      self.update()
  
  def __repr__(self):
    table_cols=self.table_columns()
    fieldvaluelist=""
    for fieldname in table_cols:
      column=table_cols[fieldname]
      if column['Type'][0:7]=='varchar' or column['Type']=='text' or column['Type']=='datetime':
         type='text'
      else:
        type=''
      value=GetSQLValueString(getattr(self,fieldname),type)
      if fieldvaluelist=="":          
        fieldvaluelist=fieldname+"="+value
      else:
        fieldvaluelist=fieldvaluelist+", "+fieldname+"="+value
    return fieldvaluelist
    
  def insert(self):
    table_cols=self.table_columns()
    auto_increment_field=""
    fieldlist=""
    valuelist=""
    first=True
    for fieldname in table_cols:
      column=table_cols[fieldname]
      if column['Extra']=='auto_increment':
        auto_increment_field=fieldname
      else:
        if column['Type'][0:7]=='varchar' or column['Type']=='text' or column['Type']=='datetime':
           type='text'
        else:
          type=''
        value=GetSQLValueString(getattr(self,fieldname),type)
        
        if first:
          fieldlist=fieldname
          valuelist=value
          first=False
        else :
          fieldlist=fieldlist+","+fieldname
          valuelist=valuelist+","+value
    query="insert into "+self.table_name+" ("+fieldlist+")"+" values("+valuelist+")"
    cursor=connection.cursor()
    cursor.execute(query);
    connection.commit()
    cursor.close()
    if auto_increment_field!="":
      setattr(self, auto_increment_field, cursor.lastrowid)
    return
    
  def update(self):
    table_cols=self.table_columns()
    fieldvaluelist=""
    whereclauselist=""
    first=True
    for fieldname in table_cols:
      column=table_cols[fieldname]
      if column['Type'][0:7]=='varchar' or column['Type']=='text' or column['Type']=='datetime':
         type='text'
      else:
        type=''
      value=GetSQLValueString(getattr(self,fieldname),type)
      # if fieldname=="id":
        # print first, fieldname,column['Extra'], column['Key']    
      if column['Extra']!='auto_increment' and column['Key']!="PRI":
        if fieldvaluelist=="":          
          fieldvaluelist=fieldname+"="+value
        else:
          fieldvaluelist=fieldvaluelist+","+fieldname+"="+value
      if column['Key']=="PRI":
        if whereclauselist=="":
          whereclauselist=fieldname+"="+value
        else :
          whereclauselist=whereclauselist+" and "+fieldname+"="+value
    query="update "+self.table_name+" set "+fieldvaluelist+" where "+whereclauselist
    cursor=connection.cursor()
    cursor.execute(query);
    connection.commit()
    cursor.close()
    return


class User(Table):#
    """
    Object representation of a participant in the database.
    """
    #__tablename__ = TABLE_USER
    
    # Status codes
    ALLOCATED = 1
    CONSENTED = 2
    ASSESSED = 3
    INSTRUCTED = 4
    
    id = -1#Column(Integer, primary_key=True)
    username = ""#Column(String(128))
    password = ""#Column(String(128))
    #worker = relationship("Participant",backref="user",cascade="all,delete")
    lastvisit = datetime.now()#Column(DateTime, nullable=True)
    sessionId = "" #Column(String(128), nullable=True)
    status = 1 #Column(Integer, default = 1)
    datastring = ""#Column(Text, nullable=True)
    email = ""#Column(Text, nullable=True)
    ipaddress = ""#Column(String(128), nullable=True)
    ip_in_use= ""#Column(String(1), nullable=True)
    note =  ""#Column(Text, nullable=True)
    #codes = relationship("Code",backref="user",cascade="all,delete")
    table_name='users'
      
    
    def table_columns(self):
      table_columns={
              'id':{'Extra': 'auto_increment', 'Default': None, 'Field': 'id', 'Key': 'PRI', 'Null': 'NO', 'Type': 'int(11)'},
              'username':{'Extra': '', 'Default': None, 'Field': 'username', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
              'password':{'Extra': '', 'Default': None, 'Field': 'password', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
              'lastvisit':{'Extra': '', 'Default': None, 'Field': 'lastvisit', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
              'sessionId':{'Extra': '', 'Default': None, 'Field': 'sessionId', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
              'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
              'datastring':{'Extra': '', 'Default': None, 'Field': 'datastring', 'Key': '', 'Null': 'YES', 'Type': 'text'},
              'email':{'Extra': '', 'Default': None, 'Field': 'email', 'Key': '', 'Null': 'YES', 'Type': 'text'},
              'ipaddress':{'Extra': '', 'Default': None, 'Field': 'ipaddress', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
              'ip_in_use':{'Extra': '', 'Default': None, 'Field': 'ip_in_use', 'Key': '', 'Null': 'YES', 'Type': 'varchar(1)'},
              'note':{'Extra': '', 'Default': None, 'Field': 'note', 'Key': '', 'Null': 'YES', 'Type': 'text'}
            }
      return table_columns

#Index('idx_worker_in_user', User.worker)

class Participant(Table):#(Base)
    """
    Object representation of a participant in the database.
    """
    #__tablename__ = TABLE_PARTICIPANT
    
    # Status codes
    ALLOCATED = 1
    CONSENTED = 2
    INSTRUCTED = 3
    STARTED = 4
    COMPLETED = 5
    DEBRIEFED = 6
    CREDITED = 7
    QUITEARLY = 8
    
    assignmentId = ""#Column(String(128), primary_key=True)
    workerId = ""#Column(String(128), primary_key=True)
    hitId = ""#Column(String(128))
    ipaddress = ""#Column(String(128))
    # cond = 0#Column(Integer)
    # counterbalance = 0#Column(Integer)
    # codeversion = ""#Column(String(128))
    beginhit = datetime.now()#Column(DateTime, nullable=True)
    beginexp = datetime.now()#Column(DateTime, nullable=True)
    endhit = datetime.now()#Column(DateTime, nullable=True)
    status = 1#Column(Integer, default = 1)
    debriefed = 0#Column(Boolean)
    datastring = ""#Column(Text, nullable=True)
    userid = None
    
    table_name='participants'

    def table_columns(self):
      table_columns={
            'assignmentId':{'Extra': '', 'Default': None, 'Field': 'assignmentId', 'Key': 'PRI', 'Null': 'NO', 'Type': 'varchar(128)'},
            'workerId':{'Extra': '', 'Default': None, 'Field': 'workerId', 'Key': 'PRI', 'Null': 'NO', 'Type': 'varchar(128)'},
            'hitId':{'Extra': '', 'Default': None, 'Field': 'hitId', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
            'ipaddress':{'Extra': '', 'Default': None, 'Field': 'ipaddress', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
            # 'cond':{'Extra': '', 'Default': None, 'Field': 'cond', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            # 'counterbalance':{'Extra': '', 'Default': None, 'Field': 'counterbalance', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            # 'codeversion':{'Extra': '', 'Default': None, 'Field': 'codeversion', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
            'beginhit':{'Extra': '', 'Default': None, 'Field': 'beginhit', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'beginexp':{'Extra': '', 'Default': None, 'Field': 'beginexp', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'endhit':{'Extra': '', 'Default': None, 'Field': 'endhit', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'debriefed':{'Extra': '', 'Default': None, 'Field': 'debriefed', 'Key': '', 'Null': 'YES', 'Type': 'tinyint(1)'},
            'datastring':{'Extra': '', 'Default': None, 'Field': 'datastring', 'Key': '', 'Null': 'YES', 'Type': 'text'},
            'userid':{'Extra': '', 'Default': None, 'Field': 'userid', 'Key': 'MUL', 'Null': 'YES', 'Type': 'int(11)'}
          }  
      return table_columns
"""Column(Integer, ForeignKey(TABLE_USER+'.id',
                                         use_alter=True, name='fk_participant_user_id',
                                         onupdate="CASCADE", ondelete="CASCADE"))"""
"""    
    # many to many Participant<->Game
    games = relationship('Game',
                         secondary=game_participant_table,
                         backref="participants",cascade="all,delete")
    gamesets = relationship('GameSet',
                         secondary=gameset_participant_table,
                         backref="participants",cascade="all,delete")
    choices = relationship("Choice",backref="participant",cascade="all,delete")
#Index('idx_user_in_participant', Participant.userid),

"""
class GameSet(Table):#Base
    #__tablename__ = TABLE_GAMESET
    
    UNUSED = 0
    WAITING_FOR_PARTICIPANTS = 1
    STARTED = 2
    TERMINATED = 3
    
    id = -1#Column(Integer, primary_key=True)
    status = WAITING_FOR_PARTICIPANTS#Column(Integer, default = WAITING_FOR_PARTICIPANTS)
    numExpectedParticipants = 6#Column(Integer, default = 2)
    numGames = 10#Column(Integer, default = 10)
    pic_name = ""#Column(Text, nullable=True)
    starttime = datetime.now()#Column(DateTime, nullable=True)
    playmode = ""#Column(Text, nullable=True)
    job_id = ""#Column(String(128), nullable=True)
    
    table_name='gamesets'
    
    def table_columns(self):
      table_columns={
            'id':{'Extra': 'auto_increment', 'Default': None, 'Field': 'id', 'Key': 'PRI', 'Null': 'NO', 'Type': 'int(11)'},
            'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'numExpectedParticipants':{'Extra': '', 'Default': None, 'Field': 'numExpectedParticipants', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'numGames':{'Extra': '', 'Default': None, 'Field': 'numGames', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'pic_name':{'Extra': '', 'Default': None, 'Field': 'pic_name', 'Key': '', 'Null': 'YES', 'Type': 'text'},
            'starttime':{'Extra': '', 'Default': None, 'Field': 'starttime', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'playmode':{'Extra': '', 'Default': None, 'Field': 'playmode', 'Key': '', 'Null': 'YES', 'Type': 'text'},
            'job_id':{'Extra': '', 'Default': None, 'Field': 'job_id', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
          }  
      return table_columns

    def curGameNum(self):
      #sqla curgame=db_session.query(Game.num).filter(Game.status == Game.STARTED).filter(Game.gamesetid == self.id).one()
      query="select num from games where games.status = "+GetSQLValueString(Game.STARTED,'int')+" and games.gamesetid="+GetSQLValueString(self.id,'int')
      cursor=connection.cursor(MySQLdb.cursors.DictCursor)
      cursor.execute(query)
      if cursor.rowcount==1:
        row=cursor.fetchone()
        curgamenum=row['num']
      else:
        curgamenum=-1
      cursor.close()
      return curgamenum
        
    """# many to many Game<->Participant
    #participants = relationship('Participant', secondary=Games_Participants, backref='games')

    # one to many GameSet<->Game
    games = relationship("Game",backref="gameset",cascade="all,delete")
    """

# Added by coco
class Image(Table):#Base
    
    #__tablename__ = TABLE_IMAGE
    
    #status
    FREE = 1
    USED = 2
    
    
    id = -1 #Column(Integer, primary_key=True)
    pic_name = "" #Column(String(128), nullable=True)
    percent = 0 #Column(Integer, nullable=True)   
    complexity =0 # Column(Integer, nullable=True) 
    color = "" #Column(String(128),nullable=True)
    pic_type="" #Column(String(128), nullable=False)
    status = FREE #Column(Integer, default=FREE)
    gameid = None #Column(Integer, ForeignKey(TABLE_GAME+'.id',
                                         # use_alter=True, name='fk_image_game_id',
                                         # onupdate="CASCADE", ondelete="CASCADE"))
    
    table_name='image'
    
    def table_columns(self):
      table_columns={
            'id':{'Extra': 'auto_increment', 'Default': None, 'Field': 'id', 'Key': 'PRI', 'Null': 'NO', 'Type': 'int(11)'},
            'pic_name':{'Extra': '', 'Default': None, 'Field': 'pic_name', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
            'percent':{'Extra': '', 'Default': None, 'Field': 'percent', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'complexity':{'Extra': '', 'Default': None, 'Field': 'complexity', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'color':{'Extra': '', 'Default': None, 'Field': 'color', 'Key': '', 'Null': 'YES', 'Type': 'varchar(128)'},
            'pic_type':{'Extra': '', 'Default': None, 'Field': 'pic_type', 'Key': '', 'Null': 'NO', 'Type': 'varchar(128)'},
            'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'gameid':{'Extra': '', 'Default': None, 'Field': 'gameid', 'Key': 'MUL', 'Null': 'YES', 'Type': 'int(11)'}
          }  
      return table_columns
      
#Index('idx_game_in_image', Image.gameid),

class Game(Table):#(Base)
    
    #__tablename__ = TABLE_GAME
    
    UNUSED = 0
    WAITING_FOR_PARTICIPANTS = 1
    STARTED = 2
    TERMINATED = 3
    
    id = -1 #Column(Integer, primary_key=True)
    num = 1 #Column(Integer, default = 1)
    status = WAITING_FOR_PARTICIPANTS #Column(Integer, default = WAITING_FOR_PARTICIPANTS)
    numExpectedParticipants = 0 #Column(Integer, default = 0)
    numRounds = 3 #Column(Integer, default = 3);
    datastring = "" #Column(Text, nullable=True)
    gamesetid = None #Column(Integer, ForeignKey(TABLE_GAMESET+'.id',
                                         # use_alter=True, name='fk_game_gameset_id',
                                         # onupdate="CASCADE", ondelete="CASCADE"))
    table_name='games'
    
    def table_columns(self):
      table_columns={
            'id':{'Extra': 'auto_increment', 'Default': None, 'Field': 'id', 'Key': 'PRI', 'Null': 'NO', 'Type': 'int(11)'},
            'num':{'Extra': '', 'Default': None, 'Field': 'num', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'numExpectedParticipants':{'Extra': '', 'Default': None, 'Field': 'numExpectedParticipants', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'numRounds':{'Extra': '', 'Default': None, 'Field': 'numRounds', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'datastring':{'Extra': '', 'Default': None, 'Field': 'datastring', 'Key': '', 'Null': 'YES', 'Type': 'text'},
            'gamesetid':{'Extra': '', 'Default': None, 'Field': 'gamesetid', 'Key': 'MUL', 'Null': 'YES', 'Type': 'int(11)'}
          }  
      return table_columns
    # image = relationship("Image",backref="game",cascade="all,delete")
     
    # many to many Game<->Participant
    #participants = relationship('Participant', secondary=Games_Participants, backref='games')

    # one to many Game<->Round
    #rounds = relationship("Round",backref="game",cascade="all,delete")
    
    def addImages(self,EGParameters):
      #super().__init__(self,dictionary) new style
      # old classes style
      # super(Game, self).__init__(dictionary,'')
      # super(self.__class__, self).__init__(dictionary,action)
     # Add 3 pictures to the game
    
      game_images=[]
      query="select * from image where image.status="+GetSQLValueString(Image.FREE, 'int')+" and image.pic_type="+GetSQLValueString(EGParameters['imageType'], 'text')
      cursor=connection.cursor(MySQLdb.cursors.DictCursor)
      cursor.execute(query)
      for curimage in range(0,3):
        row = cursor.fetchone()
        row['status']=Image.USED
        row['gameid']=self.id
        image=Image(row,'update')
        game_images.append(image)
      cursor.close()
      return game_images
    
    def getImagesTuple(self):
      images=[]
      query="select * from image where gameid="+GetSQLValueString(self.id, 'int')+" order by id asc"
      cursor=connection.cursor(MySQLdb.cursors.DictCursor)
      cursor.execute(query)
      for i in range(0,3):
        row = cursor.fetchone()
        image=Image(row,'select')
        images.append(image)
      cursor.close()
      return images

    def getCurRoundNum(self):
      query="select count(*) as numrounds from rounds where gameid="+GetSQLValueString(self.id, 'int')
      cursor=connection.cursor(MySQLdb.cursors.DictCursor)
      cursor.execute(query)
      row = cursor.fetchone()
      return row['numrounds']

class Round(Table):#(Base)
   
    #__tablename__ = TABLE_ROUND
    
    # status
    UNUSED = 0
    STARTED = 1
    TERMINATED = 2
    
    # type
    LONE = 0;
    SOCIAL = 1;
        
    
    id = -1#Column(Integer, primary_key=True)
    num = 1# Column(Integer, default = 1)
    status = STARTED #Column(Integer, default = 1)
    type = LONE #Column(Integer, default = LONE)
    datastring = "" #Column(Text, nullable=True)
    startTime = datetime.now() #Column(DateTime, nullable=True)
    endTime = datetime.now() #Column(DateTime, nullable=True)
    maxreward = None #Column(REAL, nullable=True)
    gameid = None #Column(Integer, ForeignKey(TABLE_GAME+'.id',
                                         # use_alter=True, name='fk_round_game_id',
                                         # onupdate="CASCADE", ondelete="CASCADE"))
    table_name='rounds'
    
    def table_columns(self):
      table_columns={
            'id':{'Extra': 'auto_increment', 'Default': None, 'Field': 'id', 'Key': 'PRI', 'Null': 'NO', 'Type': 'int(11)'},
            'num':{'Extra': '', 'Default': None, 'Field': 'num', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'type':{'Extra': '', 'Default': None, 'Field': 'type', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'datastring':{'Extra': '', 'Default': None, 'Field': 'datastring', 'Key': '', 'Null': 'YES', 'Type': 'text'},
            'startTime':{'Extra': '', 'Default': None, 'Field': 'startTime', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'endTime':{'Extra': '', 'Default': None, 'Field': 'endTime', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'maxreward':{'Extra': '', 'Default': None, 'Field': 'maxreward', 'Key': '', 'Null': 'YES', 'Type': 'double'},
            'gameid':{'Extra': '', 'Default': None, 'Field': 'gameid', 'Key': 'MUL', 'Null': 'YES', 'Type': 'int(11)'}
          }  
      return table_columns
    
    #sqla choices = relationship("Choice",backref="round",cascade="all,delete")
    
    
                           
#Index('idx_game_in_round', Round.gameid)

class Choice(Table):#(Base)
    
    id = -1 #Column(Integer, primary_key=True)
    status = 1 #Column(Integer, default = 1)
    #sqla decisions = relationship("Decision",backref="choice",cascade="all,delete")
    datastring ="" # Column(Text, nullable=True)
    roundid = None #Column(Integer, ForeignKey(TABLE_ROUND+'.id',
                                         # use_alter=True, name='fk_choice_round_id',
                                         # onupdate="CASCADE", ondelete="CASCADE"))
    
    assignmentId = "" #Column(String(128), nullable=False)
    workerId = "" #Column(String(128), nullable=False)
    
    table_name='choices'
    
    def table_columns(self):
      table_columns={
            'id':{'Extra': 'auto_increment', 'Default': None, 'Field': 'id', 'Key': 'PRI', 'Null': 'NO', 'Type': 'int(11)'},
            'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'datastring':{'Extra': '', 'Default': None, 'Field': 'datastring', 'Key': '', 'Null': 'YES', 'Type': 'text'},
            'roundid':{'Extra': '', 'Default': None, 'Field': 'roundid', 'Key': 'MUL', 'Null': 'YES', 'Type': 'int(11)'},
            'assignmentId':{'Extra': '', 'Default': None, 'Field': 'assignmentId', 'Key': 'MUL', 'Null': 'NO', 'Type': 'varchar(128)'},
            'workerId':{'Extra': '', 'Default': None, 'Field': 'workerId', 'Key': '', 'Null': 'NO', 'Type': 'varchar(128)'}
          }  
      return table_columns

#Index('idx_round_in_choice', Choice.roundid)
#Index('idx_assignment_worker_in_choice', Choice.assignmentId, Choice.workerId)

class Decision(Table):#(Base)
    
    #__tablename__ = TABLE_DECISION
    
    USER_MADE = 1;
    AUTO = 2;
    
    id = -1 #Column(Integer, primary_key=True)
    status = USER_MADE #Column(Integer, default = USER_MADE)    
    num = 0 #Column(Integer, nullable=True)
    value = 0.0 #Column(REAL, nullable=True)
    timestamp = datetime.now() #Column(DateTime, nullable=True)
    datastring = "" #Column(Text, nullable=True)
    reward = 0.0 #Column(REAL, nullable=True)
    choiceid = -1 #Column(Integer, ForeignKey(TABLE_CHOICE+'.id',
                                         # use_alter=True, name='fk_decision_choice_id',
                                         # onupdate="CASCADE", ondelete="CASCADE"))
    imageid = -1 #Column(Integer, nullable=True)
    
    table_name='decisions'
    
    def table_columns(self):
      table_columns={
            'id':{'Extra': 'auto_increment', 'Default': None, 'Field': 'id', 'Key': 'PRI', 'Null': 'NO', 'Type': 'int(11)'},
            'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'num':{'Extra': '', 'Default': None, 'Field': 'num', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'value':{'Extra': '', 'Default': None, 'Field': 'value', 'Key': '', 'Null': 'YES', 'Type': 'double'},
            'timestamp':{'Extra': '', 'Default': None, 'Field': 'timestamp', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'datastring':{'Extra': '', 'Default': None, 'Field': 'datastring', 'Key': '', 'Null': 'YES', 'Type': 'text'},
            'reward':{'Extra': '', 'Default': None, 'Field': 'reward', 'Key': '', 'Null': 'YES', 'Type': 'double'},
            'choiceid':{'Extra': '', 'Default': None, 'Field': 'choiceid', 'Key': 'MUL', 'Null': 'YES', 'Type': 'int(11)'},
            'imageid':{'Extra': '', 'Default': None, 'Field': 'imageid', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'}
          }  
      return table_columns

"""
#Index('idx_choice_in_decision', Decision.choiceid)

"""
class Questionnaire(Table):#(Base)
    
    #__tablename__ = TABLE_QUESTIONNAIRE
        
    id = -1 #Column(Integer, primary_key=True)
    status = 1 #Column(Integer, default = 1)    
    userid = -1 #Column(Integer, ForeignKey(TABLE_USER+'.id',
                                         # use_alter=True, name='fk_questionnaire_user_id',
                                         # onupdate="CASCADE", ondelete="CASCADE"))
    #gamesetid = Column(Integer, ForeignKey(TABLE_GAMESET+'.id',
    #                                     use_alter=True, name='fk_questionnaire_gameset_id',
    #                                     onupdate="CASCADE", ondelete="CASCADE"))
    gamesetid = 0 #Column(Integer, default = 0)
    enterQtime= datetime.now() #Column(datetime, nullable=True) # yyyy-mm-dd-hh-mn-sc
    leaveQtime= datetime.now() #Column(datetime, nullable=True) # yyyy-mm-dd-hh-mn-sc
    extraverted =  0 #Column(Integer, default=0)
    critical =  0 #Column(Integer, default=0)
    dependable =  0 #Column(Integer, default=0)
    anxious =  0 #Column(Integer, default=0)
    open =  0 #Column(Integer, default=0)
    reserved =  0 #Column(Integer, default=0)
    sympathetic =  0 #Column(Integer, default=0)
    disorganized =  0 #Column(Integer, default=0)
    calm =  0 #Column(Integer, default=0)
    conventional =  0 #Column(Integer, default=0)
    sexe =  0 #Column(Integer, default=0)
    nativespeakenglish =  0 #Column(Integer, default=0)
    schoolgrade =  0 #Column(Integer, default=0)
    
    table_name='questionnaires'
    
    def table_columns(self):
      table_columns={
            'id':{'Extra': 'auto_increment', 'Default': None, 'Field': 'id', 'Key': 'PRI', 'Null': 'NO', 'Type': 'int(11)'},
            'status':{'Extra': '', 'Default': None, 'Field': 'status', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'userid':{'Extra': '', 'Default': None, 'Field': 'userid', 'Key': 'MUL', 'Null': 'YES', 'Type': 'int(11)'},
            'gamesetid':{'Extra': '', 'Default': None, 'Field': 'gamesetid', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'enterQtime':{'Extra': '', 'Default': None, 'Field': 'enterQtime', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'leaveQtime':{'Extra': '', 'Default': None, 'Field': 'leaveQtime', 'Key': '', 'Null': 'YES', 'Type': 'datetime'},
            'extraverted':{'Extra': '', 'Default': None, 'Field': 'extraverted', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'critical':{'Extra': '', 'Default': None, 'Field': 'critical', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'dependable':{'Extra': '', 'Default': None, 'Field': 'dependable', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'anxious':{'Extra': '', 'Default': None, 'Field': 'anxious', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'open':{'Extra': '', 'Default': None, 'Field': 'open', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'reserved':{'Extra': '', 'Default': None, 'Field': 'reserved', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'sympathetic':{'Extra': '', 'Default': None, 'Field': 'sympathetic', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'disorganized':{'Extra': '', 'Default': None, 'Field': 'disorganized', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'calm':{'Extra': '', 'Default': None, 'Field': 'calm', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'conventional':{'Extra': '', 'Default': None, 'Field': 'conventional', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'sexe':{'Extra': '', 'Default': None, 'Field': 'sexe', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'nativespeakenglish':{'Extra': '', 'Default': None, 'Field': 'nativespeakenglish', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'},
            'schoolgrade':{'Extra': '', 'Default': None, 'Field': 'schoolgrade', 'Key': '', 'Null': 'YES', 'Type': 'int(11)'}
          }  
      return table_columns
    
"""
#Index('idx_user_in_questionnaire', Questionnaire.userid)
#Index('idx_gameset_in_questionnaire', Questionnaire.gamesetid)
"""