<?php
$httpport='';
if(isset($argv[1]))
{ $httpport=$argv[1];
} 

// duration between requests made to wsgi
$sleepingtime=300;
$base_url='http://localhost:'.$httpport.'/';
// eg static server url
$base_url_static=$base_url;
echo $base_url.'eg/robot_controler?pwd=pwdrobot_controler'.chr(10).chr(13);
while(true)
{ $url = $base_url.'eg/robot_controler?pwd=pwdrobot_controler';
	$session = curl_init($url);
	curl_setopt ($session, CURLOPT_POST, false);
	curl_setopt($session, CURLOPT_HEADER, false);
	curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
	sleep($sleepingtime);
	//echo 'robot_controler'.chr(10).chr(13);
	curl_close($session);
	sleep($sleepingtime);
}

?>
