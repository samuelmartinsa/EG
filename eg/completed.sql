select choices.workerid as workerid,games.num as gamenum,
decisions.num as decisionnum,decisions.value as decisionval
from decisions, choices, rounds, games
where decisions.choiceid=choices.id and choices.roundid=rounds.id
and rounds.gameid=games.id and rounds.num=2 and decisions.num<1
and choices.assignmentid='234'
order by gamenum,decisionnum,workerid,decisions.timestamp asc