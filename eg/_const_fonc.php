<?php 
require_once('conn_const/database.php');
require_once "Mail.php";
require_once ("Mail/mime.php");


/* if(session_id()==''){session_name($GLOBALS['rep_racine_monsite']); session_start();}
ini_set('display_errors',$display_errors);

mysql_select_db($database, $db_connection);
$aujourdhui=date("Y/m/d");

$repImage="images";
$targetself=' target="_self" ';
$targetblank=' target="_blank" '; */


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


function deconnecte_ou_connecte()
{ $codeuser='';
	if(isset($_SESSION['codeuser']))
	{ $codeuser=$_SESSION['codeuser'];
	}
	if(!isset($_SESSION['codeuser']) || $codeuser=='')
	{ http_redirect("formintranetpasswd.php?reconnexion=deconnexion");
	}
	return $codeuser;
}

function txt2type($chaine,$type)
{ if($type=='csv')
	{ $chaine=str_replace('\t',' ',$chaine);$chaine=str_replace(chr(9),' ',$chaine);
		$chaine=str_replace('\n',' ',$chaine);$chaine=str_replace(chr(13),' ',$chaine);
		$chaine=str_replace('\r',' ',$chaine);$chaine=str_replace(chr(10),' ',$chaine);
		
	}
	else if($type=='tex')
	{ $html2tex=array("&agrave;"=>"\\`a","&auml;"=>"\\\"a","&acirc;"=>"\\^a","&ccedil;"=>"\\c{c}","&egrave;"=>'\\`e',"&eacute;"=>"\\'e","&Eacute;"=>"\\'E","&ecirc;"=>"\\^e","&euml;"=>"\\\"e",
										"&icirc;"=>"\\^i","&iuml;"=>"\\\"i","&ocirc;"=>"\\^o","&ouml;"=>"\\\"o","&ugrave;"=>"\\`u","&uuml;"=>"\\\"u","&ucirc;"=>"\\^u",
										"&laquo;"=>"","&raquo;"=>"","&quot;"=>"'","&deg;"=>"","%"=>"\\%","_"=>"\\_*",
										"&amp;"=>"&",
										"&#946;"=>"",
										"&gamma;"=>"",
										"&"=>"\\&"
										);
		$chaine=htmlentities($chaine);
		foreach($html2tex as $carhtml=>$cartex)
		{ $chaine=str_replace($carhtml,$cartex,$chaine);
		}
	}
	return $chaine;
}

function js_tab_val($val)
{ return str_replace(array(chr(10),chr(13),'"',"&rsquo;"),array('\n','\r','\"',"'",),str_replace(chr(92),chr(92).chr(92),$val));
}

function html2js($val)
{ return str_ireplace(array("<br>","'"),array("\\n","\'"), html_entity_decode($val));
}

