<?php

//cmd_bonus = "curl -X POST --data-urlencode \"amount=" + amount + "\" https://api.crowdflower.com/v1/jobs/"+job_id+"/workers/"+cwf_contributor_id+"/bonus.json?key="+api_key
$hostname = "localhost";
$database = "eg_test";
$username = "root";
$password = "root";
$db_connection= mysql_connect($hostname, $username, $password) or trigger_error(mysql_error(),E_USER_ERROR); 
mysql_select_db($database, $db_connection);
//$api_key = "vir74DJsY4m5Jz6BwcM-";
// $job_id = "";//930744
//$url = "https://api.crowdflower.com/v1/jobs/".$job_id."/workers/".$cwf_contributor_id."/bonus.json?key=".$api_key;
$url="http://localhost/tests/reponse_wsgi.php";
$EGParameters['job_id']='111';
$query_rs= "select keyCodeBegin, keyCodeEnd, users.username as cwf_contributor_id,".
            " keycode_gameset_user.status, keycode_gameset_user.bonus".
            " from keycode_gameset_user,users,gamesets".
            " where keycode_gameset_user.userid=users.id".
            " and keycode_gameset_user.gamesetid=gamesets.id".
            " and gamesets.job_id='".$EGParameters['job_id']."'".
            " and keycode_gameset_user.status='USED'".
            " order by keycode_gameset_user.gamesetid,users.username asc";
echo $query_rs;
$rs=mysql_query($query_rs);
echo mysql_num_rows($rs);
$i=0;
while($row_rs=mysql_fetch_assoc($rs))
{ # Send a bonus
	$i++;
	$cwf_contributor_id = $row_rs['cwf_contributor_id'];//21619284=contibutor in job 930744//38656039//40167322"123"
	$amount = urlencode("0"); # in cents
	$session = curl_init($url);
	curl_setopt ($session, CURLOPT_POST, true);
	curl_setopt ($session, CURLOPT_POSTFIELDS, array('amount'=>$amount));
	curl_setopt($session, CURLOPT_HEADER, false);// Don't return HTTP headers.
	curl_setopt($session, CURLOPT_RETURNTRANSFER, true);//  Do return the contents of the call
	curl_setopt($session, CURLOPT_SSL_VERIFYPEER, false);
	//curl_setopt($session, CURLOPT_PUT, false);
	//curl_setopt($session, CURLOPT_VERBOSE, true);
	$pay_result[$cwf_contributor_id] = curl_exec($session);// Make the call
	curl_close($session);
	echo $cwf_contributor_id.'pay_result'.$pay_result[$cwf_contributor_id];
  if(strpos($pay_result[$cwf_contributor_id],"success")!==false)
  { $query_rs="update keycode_gameset_user set status='USED' where keyCodeBegin=".GetSQLValueString($row_rs['keyCodeBegin'], 'text');
    echo $query_rs;
    mysql_query($query_rs);
	} /* */
}

function getChamp($texte,$champ)
{ $posdeb=strpos($texte,"<".$champ.">");
  if($posdeb)
  { $posdeb=$posdeb+strlen("<".$champ.">");
    $posfin=strpos($texte,"</".$champ.">",$posdeb)-1;
    if($posfin)
    { return substr($texte,$posdeb,$posfin-$posdeb+1);
    }
  }
  return "";
}

// Open the Curl session
/*$session = curl_init($url);
curl_setopt ($session, CURLOPT_POST, false);
// Don't return HTTP headers. Do return the contents of the call
curl_setopt($session, CURLOPT_HEADER, false);
curl_setopt($session, CURLOPT_RETURNTRANSFER, true);

// Make the call
 echo "Appel a hal url=".$url."\n";
$xml = curl_exec($session);
$posdeb_halsid=strpos($xml,'name="halsid"');
$posdeb_halsid=strpos($xml,'value="',$posdeb_halsid)+7;
$posfin_halsid=strpos($xml,'"',$posdeb_halsid)-1;
$halsid=substr($xml,$posdeb_halsid,$posfin_halsid-$posdeb_halsid+1); 
// Hal returns HTML. Set the Content-Type appropriately
//header("Content-Type: text/html");

//echo $xml;
//echo $halsid;
curl_close($session);*/
?>
