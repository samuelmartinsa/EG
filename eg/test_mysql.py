#import mysql.connector
import random
import MySQLdb
from datetime import datetime, timedelta
from db_no_sqla import init_db,free_images,generateNewKeyCodes,connection,serious_workers_have_chosen,\
                get_db_keys_users_gamesets,db_get_free_keys, get_db_users_gamesets,db_get_decision,db_get_user,\
                clean_tables_after_end_on_start,GetSQLValueString,get_EG_session_info,dump_db,\
                select_and_create_games, check_for_enough_games, pay_participants, view_participants_of_a_job_id
 
from models_no_sqla import Participant, Game, GameSet, Round, Choice, Decision, User, Questionnaire, Code, Image#,keycode_gameset_user
EGParameters=dict()
EGParameters['imageType']='peanut'
#paramMysql = {'host':"localhost",'user':"root",'passwd':"root", 'db':"eg_test_no_sqla"}
#conn = MySQLdb.connect(**paramMysql)
cursor = connection.cursor(MySQLdb.cursors.DictCursor)
"""cursor.execute("show columns from questionnaires")
rs=cursor.fetchall()
for row in rs:
  print row
  #user=User(row)"""

cursor.execute("select * from games where id=1")
row = cursor.fetchone()
x=Game(row,'select')
images= x.getImagesTuple()
for i in range(0,3):
  print images[i]
color=[]
for i in range(0,3):
  color.append(images[i].pic_name)
for i in range(0,3):
  print color[i]

#print color
# tab_decision=dict()
# for i in range(0,3):
  # tab_decision[i]={'auto':random.randint(0,2),'value':random.randint(0,500)}
# for i in range(0,3):
  # print tab_decision[i]['auto']


connection.close()

