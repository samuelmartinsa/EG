from subprocess import Popen, PIPE
import os

api_key = "vir74DJsY4m5Jz6BwcM-";
url = "\"https://api.crowdflower.com/v1/jobs.json?key="+api_key+"\"";
title = "test_for_bonus";
title_cmd = "\"job[title]="+title+"\"";
result=''
for i in range(1,5):
  # Send a bonus
  cwf_player_id = str(i)#"123"#21619284
  job_id = "111"#930744
  amount = "0"
  cmd_bonus = "curl -k -X POST --data-urlencode \"amount=" + amount + "\" https://api.crowdflower.com/v1/jobs/"+job_id+"/workers/"+cwf_player_id+"/bonus.json?key="+api_key
  print cmd_bonus
  proc=Popen(cmd_bonus, stdout = PIPE, shell=True)
  (out, err) = proc.communicate()
  print i,"program output:", out
print 'test'
  # for line in stream.stdout:
    # #print str(i)+line
    # result=result+str(i)+line
# print 'result'
# print result