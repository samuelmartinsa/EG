<?php
$base_url='http://localhost:8080/';
$url = $base_url.'eg/expconsensus?hitId='.'1'.'&assignmentId='.'1'.'&workerId='.'1'.'&sessionId='.'1';
			$tab_postdata=array('decision0'=>''.rand(1,100).'','decision1'=>''.rand(1,100).'','decision2'=>''.rand(1,100).'','auto0'=>'1','auto1'=>'1','auto2'=>'1');
			var_dump($tab_postdata);
			$session = curl_init($url);
			curl_setopt ($session, CURLOPT_POST, true);
			curl_setopt($session, CURLOPT_HEADER, false);
			curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
			curl_setopt ($session, CURLOPT_POSTFIELDS,$tab_postdata);
			$html = curl_exec($session);
			curl_close($session);
			print $html;
?>