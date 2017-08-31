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
$datebegin=isset($_GET['datebegin'])?$_GET['datebegin']:"";
$dateend=isset($_GET['dateend'])?$_GET['dateend']:"";
$database = isset($_GET['database'])?$_GET['database']:"eg";

mysql_select_db($database, $db_connection);
$lastgamesetstarttime_user=array();
$where_clause="";
if($datebegin!='')
{ if($dateend!='')
	{ $where_clause=" AND SUBSTRING(gamesets.starttime,1,10)<=".GetSQLValueString($dateend, 'text').
									" AND SUBSTRING(gamesets.starttime,1,10)>=".GetSQLValueString($datebegin, 'text'); 
	}
	else
		$where_clause=" AND SUBSTRING(gamesets.starttime,1,10)=".GetSQLValueString($datebegin, 'text');
}
$query_rs= " select max(gamesets.starttime) as lastgamesettime,workerId as userid from gamesets, participants".
					" where gamesets.id=0+participants.assignmentId".
					$where_clause.
					" group by workerId";
//echo $query_rs.chr(13);				
$rs=mysql_query($query_rs);
while($row_rs=mysql_fetch_assoc($rs))
{ $lastgamesetstarttime_user[''.$row_rs['userid']]=$row_rs['lastgamesettime'];
//echo $lastgamesetstarttime_user[''.$row_rs['userid']].' '.$row_rs['userid'].chr(13);
}

$query_rs= " SELECT distinct users.id AS userid,users.username, users.email AS email,users.note,ipaddress,if(totalreward IS NULL,'',totalreward) as totalreward,enterQtime,leaveQtime,extraverted,".
						" critical, dependable, anxious, open, reserved, sympathetic, disorganized, calm,conventional, sexe, nativespeakenglish,schoolgrade".
						" FROM users ".
						" LEFT JOIN questionnaires ON users.id=questionnaires.userid".
						" LEFT JOIN keycode_gameset_user ON  users.id=keycode_gameset_user.userid".
						" ORDER BY userid";
//echo $query_rs.chr(13);				
$rs=mysql_query($query_rs);
//echo mysql_num_rows($rs).chr(13);				

header('Content-type: text/plain');
echo 'userid'."\t".'username'."\t".'email'."\t".'note'."\t".'ipaddress'."\t".'totalreward'."\t".'enterQtime'."\t".'leaveQtime'."\t".'extraverted'."\t".'critical'."\t".'dependable'."\t".'anxious'."\t".'open'."\t".'reserved'."\t".'sympathetic'."\t".'disorganized'."\t".
													'calm'."\t".'conventional'."\t".'sexe'."\t".'nativespeakenglish'."\t".'schoolgrade'."\t".'last gameset time'."\n";
while($row_rs=mysql_fetch_assoc($rs))
{ //echo 'a'.$row_rs['userid'].chr(13); 
	if(array_key_exists(''.$row_rs['userid'],$lastgamesetstarttime_user))
	{ $first=true;
	  $tab=$row_rs;
		foreach($tab as $field=>$val)
		{ $value=''.$val;
			$value=str_replace(chr(13), " ",$value);
			$value=str_replace(chr(10), " ",$value);
			$value=str_replace(chr(9), " ",$value);
			echo ($first?"":"\t").$value;
			$first=false;
		}
		echo "\t".$lastgamesetstarttime_user[''.$row_rs['userid']]."\n";
	}
}

?>