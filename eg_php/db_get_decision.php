<?php require_once('db_connection.php'); ?>
<?php
function GetSQLValueString($theValue, $theType, $theDefinedValue = "", $theNotDefinedValue = "") 
{
  if (PHP_VERSION < 6) {
    $theValue = get_magic_quotes_gpc() ? stripslashes($theValue) : $theValue;
  }

  $theValue = function_exists("mysql_real_escape_string") ? mysql_real_escape_string($theValue) : mysql_escape_string($theValue);

  switch ($theType) {
    case "text":
      $theValue = ($theValue != "") ? "'" . $theValue . "'" : "''";// PG : "''" au lieu de "NULL"
      break;    
    case "long":
    case "int":
      $theValue = ($theValue != "") ? intval($theValue) : "NULL";
      break;
    case "double":
      $theValue = ($theValue != "") ? doubleval($theValue) : "NULL";
      break;
    case "date":
      $theValue = ($theValue != "") ? "'" . $theValue . "'" : "NULL";
      break;
    case "defined":
      $theValue = ($theValue != "") ? $theDefinedValue : $theNotDefinedValue;
      break;
  }
  return $theValue;
}
// localhost/eg_php/db_get_decision.php?datebegin=2016-03-07&dateend=2016-03-08&playmode=continuous&database=eg_test
$datebegin=isset($_GET['datebegin'])?$_GET['datebegin']:"";
$dateend=isset($_GET['dateend'])?$_GET['dateend']:"";
$playmode=isset($_GET['playmode'])?$_GET['playmode']:"continuous";
$database = isset($_GET['database'])?$_GET['database']:"eg";

mysql_select_db($database, $db_connection);

$where_clause="";
if($datebegin!='')
{ if($dateend!='')
	{ $where_clause=" AND SUBSTRING(gamesets.starttime,1,10)<=".GetSQLValueString($dateend, 'text').
								 " AND SUBSTRING(gamesets.starttime,1,10)>=".GetSQLValueString($datebegin, 'text'); 
	}
	else
	{
	 $where_clause=" AND SUBSTRING(gamesets.starttime,1,10)=".GetSQLValueString($datebegin, 'text');
	}
}
if($playmode=='continuous')
{ $where_clause.=" AND decisions.num=0";
}
$query_rs= "SELECT gamesets.id AS gameset_id, games.id AS game_id,games.num as game_num, rounds.id AS round_id,rounds.num as round_num,".
					" rounds.startTime as round_starttime, rounds.endTime as round_endtime,  decisions.num AS decision_num, image.id AS image_id,".
					" image.pic_name AS pic_name, image.complexity AS image_complexity, image.color AS image_color, image.percent AS image_percent,".
					" choices.workerId AS workerId,decisions.value AS decision_value,decisions.reward AS decision_reward,decisions.status AS decision_status, decisions.timestamp".
					" FROM gamesets, games, rounds, choices, decisions, image ".
					" WHERE gamesets.id = games.gamesetid".
					" AND games.id = rounds.gameid".
					" AND rounds.id = choices.roundid ".
					" AND choices.id = decisions.choiceid".
					" AND decisions.imageid = image.id ".
					$where_clause.
					" ORDER BY gamesets.id,game_num,round_num,decision_num,workerId";
$rs=mysql_query($query_rs);
//echo $query_rs;
header('Content-type: text/plain');
$fieldlist=array('gameset_id','game_id','game_num','round_id','round_num','round_starttime','round_endtime','decision_num','image_id','pic_name','image_complexity','image_color','image_percent',
                            'workerId','decision_value','decision_reward','decision_status','timestamp');

foreach($fieldlist as $field)
{ echo $field."\t";
}
echo "\n";
	
while($row_rs=mysql_fetch_assoc($rs))
{ foreach($fieldlist as $field)
	{ echo $row_rs[$field]."\t";
	}
	echo "\n";
}
?>