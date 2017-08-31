<?php
$httpport='';
if(isset($argv[1]))
{ $httpport=$argv[1];
}
// login time range to connect
$logintime=rand(0,10);//0;
// get all files (images, css, js, ...). Default=no
$multiget=false;//true;
/* if((isset($argv[1]) && $argv[1]!='mg')
{ $multiget=false;
} */
// eg dynamic server url
$base_url='http://localhost:'.$httpport.'/';//'http://195.220.155.5:8080/';
//echo $base_url.'eg/robot_controler?pwd=pwdrobot_controler';
// eg static server url
$base_url_static=$base_url;//'http://localhost:8080/';
$url = $base_url.'eg/login';
//echo 'eg robot client started'.($multiget?' with multi_get option':'').chr(10).chr(13);
$html='';
$end=false;
$tab_step=array('askforuserkeycode'=>false,'login'=>false,'consent'=>false,'questionnaire_first'=>false,
								'instruct'=>false,'wait_in_room'=>false,'expconsensus'=>false,'debriefing'=>false);
$skipConsentInstruct=false;
$tab_json_userkeycode=array();
$tab_postdata=array();
$tab_field=array();
//list of all url get by using do_multiget
//try to simulate the client browser and doesn't get already loaded files
$tab_curl_already_get=array();
$hitId='';$assignmentId='';$workerId='0';$sessionId='';
$i=0;
sleep($logintime);
while(!$end)
{ if(!$tab_step['askforuserkeycode'])// Ask wsgi for username, keycode,.....
	{ $url = $base_url.'eg/login?robot=askforuserkeycode';
		$session = curl_init($url);
		curl_setopt ($session, CURLOPT_POST, false);
		curl_setopt($session, CURLOPT_HEADER, false);
		curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
		$html = curl_exec($session);
		$tab_json_userkeycode=json_decode($html, true);
		if(isset($tab_json_userkeycode['loginsignin']) && $tab_json_userkeycode['loginsignin']=='robot')
		{ $tab_step['askforuserkeycode']=true;
			if(isset($tab_json_userkeycode['skipConsentInstruct']) && strtolower($tab_json_userkeycode['skipConsentInstruct']=='y'))
			{ $skipConsentInstruct=true;
				$tab_step['consent']=true;
				$tab_step['questionnaire_first']=true;
				$tab_step['instruct']=true;
			}
		}
	}
	else if(!$tab_step['login'])
	{ $url = $base_url.'eg/login';
		$session = curl_init($url);
		curl_setopt ($session, CURLOPT_POST, true);
		curl_setopt($session, CURLOPT_HEADER, false);
		curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
		$tab_postdata=array('keyCodeBegin'=>$tab_json_userkeycode['keyCodeBegin'],'username'=>$tab_json_userkeycode['username'],'loginsignin'=>'robot','pwd'=>'');
		curl_setopt ($session, CURLOPT_POSTFIELDS,$tab_postdata);
		$html = curl_exec($session);
		curl_close($session);
		//do_multiget($html,$multiget,$base_url_static,$base_url.'eg/login');
		$tab_postdata=find_fields_in_form($html);
		$workerId=$tab_postdata['workerId'];$sessionId=$tab_postdata['sessionId'];
		if(strpos($html,'<title>Consent Form</title>')!==false || $skipConsentInstruct)
		{ $tab_step['login']=true;
			echo 'in robot_eg : login OK'.chr(10).chr(13);
		}
	}
	else if(!$tab_step['consent'])
	{ $tab_postdata=find_fields_in_form($html);
		$hitId=$tab_postdata['hitId'];$assignmentId=$tab_postdata['assignmentId'];$workerId=$tab_postdata['workerId'];$sessionId=$tab_postdata['sessionId'];
		$url = $base_url.'eg/consent?hitId='.$hitId.'&assignmentId='.$assignmentId.'&workerId='.$workerId.'&sessionId='.$sessionId;
		$session = curl_init($url);
		curl_setopt ($session, CURLOPT_POST, true);
		curl_setopt($session, CURLOPT_HEADER, false);
		curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
		curl_setopt ($session, CURLOPT_POSTFIELDS,$tab_postdata);
		$html = curl_exec($session);
		curl_close($session);
		//do_multiget($html,$multiget,$base_url_static,$base_url.'eg/consent');
		$tab_step['consent']=true;
	}
	else if(!$tab_step['questionnaire_first'])
	{ $tab_postdata=find_fields_in_form($html);
		$url = $base_url.'eg/questionnaire_first?hitId='.$hitId.'&assignmentId='.$assignmentId.'&workerId='.$workerId.'&sessionId='.$sessionId.'&robot=';
		$session = curl_init($url);
		curl_setopt ($session, CURLOPT_POST, true);
		curl_setopt($session, CURLOPT_HEADER, false);
		curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
		curl_setopt ($session, CURLOPT_POSTFIELDS,$tab_postdata);
		$html = curl_exec($session);
		curl_close($session);
		//do_multiget($html,$multiget,$base_url_static,$base_url.'eg/questionnaire_first');
		$tab_step['questionnaire_first']=true;
	}
	else if(!$tab_step['instruct'])
	{ $tab_postdata=find_fields_in_form($html);
		$url = $base_url.'eg/instruct?hitId='.$hitId.'&assignmentId='.$assignmentId.'&workerId='.$workerId.'&sessionId='.$sessionId.'&robot=';
		$session = curl_init($url);
		curl_setopt ($session, CURLOPT_POST, true);
		curl_setopt($session, CURLOPT_HEADER, false);
		curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
		curl_setopt ($session, CURLOPT_POSTFIELDS,$tab_postdata);
		$html = curl_exec($session);
		curl_close($session);
		//do_multiget($html,$multiget,$base_url_static,$base_url.'eg/instruct');
		$tab_step['instruct']=true;
	}
	else if(!$tab_step['wait_in_room'])
	{ //echo 'wait_in_room assignmentId '.$assignmentId.chr(10).chr(13);
		if($assignmentId=='0' || $assignmentId==0 || $assignmentId=='')
		{ $url = $base_url.'eg/waitingroom?hitId='.$hitId.'&assignmentId='.$assignmentId.'&workerId='.$workerId.'&sessionId='.$sessionId.'&time='.time().'&robot=';
			echo $url.chr(10).chr(13);
			$session = curl_init($url);
			curl_setopt ($session, CURLOPT_POST, false);
			curl_setopt($session, CURLOPT_HEADER, false);
			curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
			$html = curl_exec($session);
			curl_close($session);
			//do_multiget($html,$multiget,$base_url_static,$base_url.'eg/waitingroom');
			//echo $html;
			$pos=strpos($html,"assignmentId='");
			if($pos!==false)
			{ $pos=strpos($html,"'",$pos+1);
				$pos_end=strpos($html,"'",$pos+1);
				$assignmentId=substr($html,$pos+1,$pos_end-$pos-1);
				$hitId=$assignmentId;
				//echo 'assignmentId='.$assignmentId.chr(10).chr(13);
			}
		}
		else
		{ $url = $base_url.'eg/waitingroom?getFlag=true&hitId='.$hitId.'&assignmentId='.$assignmentId.'&workerId='.$workerId.'&sessionId='.$sessionId.'&time='.time().'&robot=';
			$session = curl_init($url);
			curl_setopt ($session, CURLOPT_POST, false);
			curl_setopt($session, CURLOPT_HEADER, false);
			curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
			$html = curl_exec($session);
			curl_close($session);
			//do_multiget($html,$multiget,$base_url_static,$base_url.'eg/waitingroom');
			//echo $html;
			$tab_json=json_decode($html, true);
			if(isset($tab_json['status']))
			{ //echo "tab_json['status'] : ".$tab_json['status'].chr(10).chr(13);
				if($tab_json['status']=='closeWait_in_room' || $tab_json['status']=='EG_NOT_RUNNING') 
				{ //echo $tab_json['status'].chr(10).chr(13);
					$end=true;
				}
				else if($tab_json['status']=='Wait_in_room')
				{ sleep(5);//sleep(1);
					//echo 'Wait_in_room robot '.$workerId.chr(10).chr(13);
				}
				else if($tab_json['status']=='GameSet_STARTED')
				{	//echo 'in robot_eg : GameSet_STARTED OK for workerId='.$workerId.chr(10).chr(13);
					$tab_step['wait_in_room']=true;
				}
			}
		}
	}
	else if(!$tab_step['expconsensus'])
	{ $url = $base_url.'eg/expconsensus?getFlag=true&hitId='.$hitId.'&assignmentId='.$assignmentId.'&workerId='.$workerId.'&sessionId='.$sessionId.'&time='.time().'&robot=';
		$session = curl_init($url);
		curl_setopt ($session, CURLOPT_POST, false);
		curl_setopt($session, CURLOPT_HEADER, false);
		curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
		$html = curl_exec($session);
		curl_close($session);
		$tab_json=json_decode($html, true);
		// load first files as static 
		//do_multiget($html,$multiget,$base_url_static,$base_url.'eg/expconsensus');
		// and then load dynamic images 
		$htmlimage='';
		/* foreach($tab_imageurl as $numimage=>$imageurl)
		{ $htmlimage.='<img src="'.$imageurl.'">'.chr(10).chr(13);
		} */
		if($tab_json['status']=="EG_NOT_RUNNING")
		{ echo ' EG_NOT_RUNNING : end workerId '.$workerId.chr(10).chr(13);
			$end=true;
		}
		else
		{	if(!isset($current_game))
			{ $current_game=-1;
			}
			if(!isset($current_round))
			{ $current_round=-1;
			}
			// post data
			if($tab_json['status']=='CHOICE_TO_BE_MADE')
			{	if(isset($tab_json['givenanswers']))
				{ $decisiontime=$tab_json['decisiontime'];
					$tab_decisions=explode('#',$tab_json['decisions']);
					//echo 'In robot given decision : '.implode($tab_decisions)." decisiontime : ".$decisiontime.chr(10).chr(13);				
				}
				else
				{ $decisiontime=rand(10,30);
					$tab_decisions=array(''.rand($tab_json['minDecisionValue'],$tab_json['maxDecisionValue']).'',''.rand($tab_json['minDecisionValue'],$tab_json['maxDecisionValue']).'',''.rand($tab_json['minDecisionValue'],$tab_json['maxDecisionValue']).'');
					//echo 'In robot random decision : '.implode($tab_decisions);
				}
				sleep($decisiontime);
				$current_game=$tab_json['game'];
				$current_round=$tab_json['round'];
				$url = $base_url.'eg/expconsensus?&hitId='.$hitId.'&assignmentId='.$assignmentId.'&workerId='.$workerId.'&sessionId='.$sessionId;
				$tab_postdata=array('roundNum'=>$current_round,'decision0'=>$tab_decisions[0],'decision1'=>$tab_decisions[1],'decision2'=>$tab_decisions[2],'auto0'=>'2','auto1'=>'2','auto2'=>'2');
				$session = curl_init($url);
				curl_setopt ($session, CURLOPT_POST, true);
				curl_setopt($session, CURLOPT_HEADER, false);
				curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
				curl_setopt ($session, CURLOPT_POSTFIELDS,$tab_postdata);
				$html = curl_exec($session);
				curl_close($session);
			}
			if($tab_json['status']=='GAMESET_OVER')
			{	$tab_step['expconsensus']=true;
			}
		}
	}
	else if(!$tab_step['debriefing'])
	{ $url = $base_url.'eg/debriefing?hitId='.$hitId.'&assignmentId='.$assignmentId.'&workerId='.$workerId.'&sessionId='.$sessionId.'&time='.time().'&robot=';
		$session = curl_init($url);
		curl_setopt ($session, CURLOPT_POST, false);
		curl_setopt($session, CURLOPT_HEADER, false);
		curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
		$html = curl_exec($session);
		curl_close($session);
		//do_multiget($html,$multiget,$base_url_static,$base_url.'eg/debriefing');
		//echo 'workerId='.$workerId.chr(10).chr(13).'debriefing OK'.chr(10).chr(13);
		$tab_step['debriefing']=true;
	}
	else
	{ $end=true;
	}
	sleep(1);
	//echo 'while robot'.(isset($workerId)?' workerId'.$workerId:'').chr(10).chr(13);
	$i++;
} /**/

function find_fields_in_form($html)
{ $tab_field=array();
	$eof=false;
	$nextpos=0;
	while(!$eof)
	{ $pos=strpos($html,'input',$next_pos);
		if($pos!==false)
		{ $pos=strpos($html,'name',$pos);
			if($pos!==false)
			{ $pos_end=strpos($html,'>',$pos);
				if($pos_end!==false)
				{ $next_pos=$pos_end+1;
					$input_string=substr($html,$pos,$pos_end-$pos);
					$pos=strpos($input_string,'=');
					$pos=strpos($input_string,'"',$pos);
					$pos_end=strpos($input_string,'"',$pos+1);
					$field=substr($input_string,$pos+1,$pos_end-$pos-1);
					$pos=strpos($input_string,'value',$pos_end);
					$pos=strpos($input_string,'=',$pos);
					$pos=strpos($input_string,'"',$pos);
					$pos_end=strpos($input_string,'"',$pos+1);
					$value=substr($input_string,$pos+1,$pos_end-$pos-1);
					$tab_field[$field]=$value;
				}
				else
				{ $eof=true;
				}
			}
			else
			{ $eof=true;
			}
		}
		else
		{ $eof=true;
		}
	}
	return $tab_field;
}
exit;

function do_multiget($html,$multiget,$base_url_static,$discard_url)
{	global $tab_curl_already_get;
 	$tab_tag=array(" href", "src");
	$tab_url=array();
	$timestart=microtime(true);
	
	if($multiget)
	{ $html=str_replace(' ','',$html);
		foreach($tab_tag as $tag)
		{ $posbegin=strpos($html,$tag);
			while($posbegin!==false)
			{ if(substr($html,$posbegin+strlen($tag),1)=='=')
				{	$posbegin=strpos($html,'=',$posbegin);
					$posend=strpos($html,'>',$posbegin);
					$url=substr($html,$posbegin+1,$posend-$posbegin+1);
					//the quote separator : " or '
					$quote=substr($url,0,1);
					$url=substr($url,1);
					$posend_url=strpos($url,$quote);
					$url=substr($url,0,$posend_url);
					//discard url containing " or '
					$tab_url[]['url']=$url;
					$posbegin=strpos($html,$tag,$posend+1);
				}
				else//skip the tag
				{ $posend=$posbegin+strlen($tag);
					$posbegin=strpos($html,$tag,$posend+1);
				}
			}
		}
		foreach($tab_url as $key=>$a_tab_url)
		{ $url=ltrim($a_tab_url['url']);
			if(substr($url,0,4)!='http')
			{ $url=str_replace('..//','',$url);
				$url=str_replace('../','',$url);
				$url=$base_url_static.$url;
			}
			// to correct in html files : not important
			$tab_url[$key]['url']=str_replace('//static','/static',$url);
			if($url==$discard_url)
			{ $tab_url[$key]['discard']=true;
			}
		}
		$mh = curl_multi_init();
		foreach($tab_url as $key=>$a_tab_url)
		{ if(!$a_tab_url['discard'] && !isset($tab_curl_already_get[$a_tab_url['url']]))
			{ $tab_curl_already_get[$a_tab_url['url']]=$a_tab_url['url'];
				$tab_curl_get[$a_tab_url['url']]=curl_init();
				curl_setopt($tab_curl_get[$a_tab_url['url']], CURLOPT_URL, $a_tab_url['url']);
				curl_setopt($tab_curl_get[$a_tab_url['url']], CURLOPT_RETURNTRANSFER, true);
				curl_setopt($tab_curl_get[$a_tab_url['url']], CURLOPT_HEADER, false);
				curl_multi_add_handle($mh,$tab_curl_get[$a_tab_url['url']]);
			}
		}
		$running = null;
  	do 
		{ curl_multi_exec($mh, $running);
  	} while ($running);

		foreach($tab_url as $key=>$a_tab_url)
		{ if(!$a_tab_url['discard'])
			{ curl_multi_remove_handle($mh, $tab_curl_get[$a_tab_url['url']]);
			}
		}
		curl_multi_close($mh);
	}
}
?>
