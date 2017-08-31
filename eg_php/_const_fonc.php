<?php 
require_once('conn_const/cran.php');
include_once('conn_const/const.php');
require_once "Mail.php";
require_once ("Mail/mime.php");
include_once('_const_fonc_detail.php');
include_once('_controle_form.php');


if(session_id()==''){session_name($GLOBALS['rep_racine_site12+']); session_start();}
ini_set('display_errors',$GLOBALS['display_errors']);

mysql_select_db($database_cran, $cran);
$aujourdhui=date("Y/m/d");
$message_resultat_affiche="";//message affiche apres operation demandee par l'utilisateur

function farce($tab_param)
{ $tab_infouser=$tab_param['tab_info_user'];
	$txt='';
	if($tab_infouser['nom']=='zzzzz' && $tab_infouser['prenom']=='zzzzzz' && date("Y/m/d")=='2015/03/02' && date("H")>='99')
	{ 
		if(isset($tab_param['prog']) && $tab_param['prog']=='menuprincipal')
		{ if(isset($tab_param['quoi']) && $tab_param['quoi']=='image') 
			{ $txt='<img src="images/farce/0.png">';
			}
			else if(isset($tab_param['quoi']) && $tab_param['quoi']=='curseur') 
			{ $txt='document.body.style.cursor=\'url(\\\'images/farce/12.png\\\'), auto\';';
			}
		}
		else if(isset($tab_param['prog']) && ($tab_param['prog']=='gestionindividus' || $tab_param['prog']=='gestioncontrats'))
		{ if(isset($tab_param['quoi']) && $tab_param['quoi']=='curseur') 
			{ $txt='document.body.style.cursor=\'url(\\\'images/farce/'.rand(1,5).'.png\\\'), auto\';';
			}
		}
		else if(isset($tab_param['quoi']) && $tab_param['quoi']=='stylecurseurhref')
		{ $txt='<style>body a:hover { cursor : url("images/farce/a.png"), auto;}</style>';
		}
	}
	return $txt;
}


$repImage="images";
$targetself=' target="_self" ';
$targetblank=' target="_blank" ';

$etat_individu_entete=array('preaccueil'=>'PRE-ACCUEIL',
														'accueil'=>'ACCUEIL',
														'sejourpartinonvalide'=>'SEJOUR NON VISE',
														'present'=>'PERSONNEL',
														'parti'=>'PERSONNEL PARTI',
														'autre'=>'AUTRE'
														);
function checklongueur($champ,$longueurmax,$libelle)
{ return (isset($_POST[$champ]) && strlen($_POST[$champ])>$longueurmax)?"<BR>"."Longueur du champ '".$libelle."' sup&eacute;rieure &agrave; ".$longueurmax.' : '.strlen($_POST[$champ]):"";
}

function periodeencours($datedeb,$datefin)
{ return "((".$datedeb."='' or replace( ".$datedeb.", '/', '-')<=date_format(NOW(),'%Y-%m-%d')) and (".$datefin."='' or replace(  ".$datefin.", '/', '-')>=date_format(NOW(),'%Y-%m-%d')))";
}

function periodefuture($datedeb)
{ return "((".$datedeb."<>'' and replace( ".$datedeb.", '/', '-')>date_format(NOW(),'%Y-%m-%d')))";
}

function periodepassee($datefin)
{ return "((".$datefin."<>'' and replace( ".$datefin.", '/', '-')<date_format(NOW(),'%Y-%m-%d')))";
}

function intersectionperiodes($datedeb_periode1,$datefin_periode1,$datedeb_periode2,$datefin_periode2)
{ return "((".$datedeb_periode1.">=".$datedeb_periode2." and (".$datedeb_periode1."<=".$datefin_periode2." or ".$datefin_periode2."=''))".
					" or (".$datefin_periode1.">=".$datedeb_periode2." and (".$datefin_periode1."<=".$datefin_periode2." or ".$datefin_periode2."=''))".
					" or (".$datedeb_periode2.">=".$datedeb_periode1." and (".$datedeb_periode2."<=".$datefin_periode1." or ".$datefin_periode1."=''))".
					" or (".$datefin_periode2.">=".$datedeb_periode1." and (".$datefin_periode2."<=".$datefin_periode1." or ".$datefin_periode1."='')))";
}
function jjmmaaaa2date($jj,$mm,$aaaa)
{ if((int)$jj<1 || (int)$jj>31 || (int)$mm<1 || (int)$mm>12 || (int)$aaaa<1900 || strlen($aaaa)!=4)
  { return "";
  }
  else
  { return $aaaa."/".str_pad($mm,2,"0",STR_PAD_LEFT)."/".str_pad($jj,2,"0",STR_PAD_LEFT);
  }
}
function hhmn2heure($hh,$mn)
{ if((int)$hh<0 || (int)$hh>23 || (int)$mn<0 || (int)$mn>60 || (int)$hh==0)
  { return "";
  }
  else
  { return str_pad($hh,2,"0",STR_PAD_LEFT)."H".str_pad($mn,2,"0",STR_PAD_LEFT);
  }
}

function aaaammjj2jjmmaaaa($aaaammjj,$separateur)
{ return strlen($aaaammjj)==10?substr($aaaammjj,8,2).$separateur.substr($aaaammjj,5,2).$separateur.substr($aaaammjj,0,4):"";
}

function est_date($jj,$mm,$aaaa)
{ if($jj.$mm.$aaaa=='')//tous les champs vides : OK
	{ return true;
	}
	else if($jj=='' || $mm=='' || $aaaa=='')//un champ vide et jj+mm+aaaa pas vide : pas OK
  { return false;
	}
	else
	{ $tab_nbjours_du_mois=$GLOBALS['nb_jours_du_mois'];
		$unjourbissextile=((int)$aaaa%4==0 && (int)$mm==2)?1:0;
		if(!isset($tab_nbjours_du_mois[(int)$mm]))
		{ return false;
		}
		else
		{ if($jj<1 || $jj >$tab_nbjours_du_mois[(int)$mm]+$unjourbissextile || (strlen($aaaa) >=3 && (int)$aaaa <1900) || !(int)($jj) || !(int)($mm) || !(int)($aaaa))
			{ return false;
			}
			else
			{ return true;
			}
		}
	}
}

function est_heure_mn($hh,$mn)
{ if($hh.$mn=='')//tous les champs vides : OK
	{ return true;
	}
	else//comparaison chaine car pbl avec int et la valeur "0" 
	{ if($hh<"00" || $hh>"23" || $mn<"00" || $mn>"60" || !is_numeric($hh) || !is_numeric($mn))
		{ return false;
		}
		else
		{ return true;
		}
	}
}

function est_champ_annee($champ_annee)
{ if($champ_annee!='')
	{ if(!(int)($champ_annee) || strlen($champ_annee)!=4) 
		{
		return false;
		}
		else
		{ return true;
		}
	}
	else
	{ return true;
	}
}

function est_mail($mail) 
{ if($mail=='') return true;
  if ((strpos($mail,'@')!==false && (strpos($mail,'.'))>=0))  return true;
	else return false;
}

function estrole($codelibrole,$tab_roleuser)
{ foreach($tab_roleuser as $codelibroleaction=>$val)
	{ $tab=explode('#',$codelibroleaction);
		if($codelibrole==$tab[0])
		{ return true;
		}
	}
	return false;
}

function calcule_annee_these($date_preminscr,$date_soutenance,$ajustement)
{ /* $moisdeb_these=substr($datedeb_these,5,2); */
	$mois_preminscr=substr($date_preminscr,5,2);
	$annee_preminscr=substr($date_preminscr,0,4);
	$mois_soutenance=substr($date_soutenance,5,2);
	$annee_soutenance=substr($date_soutenance,0,4);
	if($annee_soutenance=='')
	{ $mois_courant=date('m');
		$annee_courant=date('Y');
	}
	else
	{ $mois_courant=$mois_soutenance;
		$annee_courant=$annee_soutenance;
	}
	$annee_octprecedent=$annee_preminscr;
	if($mois_preminscr>=1 && $mois_preminscr<=9)
	{ $annee_octprecedent--;
	}
	$num_annee=$annee_courant-$annee_octprecedent;
	if($mois_courant>=10 && $mois_courant<=12) 
	{ $num_annee++;	
	}
	$num_annee+=$ajustement;
	return $num_annee;
}

function duree_aaaammjj($datedeb, $datefin)
{ $tab_nbjours_du_mois=$GLOBALS['nb_jours_du_mois'];
	$jourdeb=intval(substr($datedeb,8,2));
	$jourfin=intval(substr($datefin,8,2));
	$moisdeb=intval(substr($datedeb,5,2));
	$moisfin=intval(substr($datefin,5,2));
	$anneedeb=intval(substr($datedeb,0,4));
	$anneefin=intval(substr($datefin,0,4));
	$jourdebbissextile=($anneedeb%4==0 && $moisdeb==2)?1:0;
	$jourfinbissextile=($anneefin%4==0 && $moisfin==2)?1:0;
	$nbjours=0;
	$nbmois=0;
	$nbannees=$anneefin-$anneedeb;
	if(est_date($jourdeb,$moisdeb,$anneedeb) && est_date($jourfin,$moisfin,$anneefin) && $datedeb!='' && $datefin!='' && $datedeb<=$datefin && $jourdeb<=$tab_nbjours_du_mois[$moisdeb]+$jourdebbissextile && $jourfin<=$tab_nbjours_du_mois[$moisfin]+$jourfinbissextile)
	{ if($moisfin-$moisdeb<0)
		{	$nbmois=$moisfin+12-$moisdeb;
			$nbannees-=1;
		}
		else
		{ $nbmois=$moisfin-$moisdeb;
		}
		if($jourfin!=$jourdeb-1)
		{ $nbjours=($tab_nbjours_du_mois[$moisdeb]+$jourdebbissextile-$jourdeb+1)+$jourfin;
			if($nbjours>=$tab_nbjours_du_mois[$moisdeb]+$jourfinbissextile)
			{ $nbjours=$nbjours-($tab_nbjours_du_mois[$moisdeb]+$jourfinbissextile);
				if($nbjours>=$tab_nbjours_du_mois[$moisfin]+$jourfinbissextile)
				{ $nbjours=$nbjours-($tab_nbjours_du_mois[$moisfin]+$jourfinbissextile);
					$nbmois++;
				}
			}
			else
			{ $nbmois--;
			}
		}
		if($nbmois==12)
		{ $nbmois=0;
			$nbannees+=1;
		}
		return array("a"=>$nbannees, "m"=>$nbmois, "j"=>$nbjours);
	}
	return false;
}

function demander_autorisation($row_rs_ind,$tab_dates_individu_sejours)
{ // demander_autorisation=vrai si 
	// plus de 5 jours 
	// et pas d'autorisation depuis moins de 5 ans dans l'un des sejours precedents, sans rupture dans le temps
	$demander_autorisation=false;// l'initialisation n'a pas d'intéret par defaut car la variable est positionnee quelle que soit la situation 
	$plus_de_5_jours=false;
	$pourquoi_pas_de_demande_fsd='Pas de ZRR';
	$pourquoi_demande_fsd='';
	$datefin_sejour_prec='';
	$datefin_sejour_le_plus_recent='';
	$date_derniere_autorisation='';
	$num_sejour_derniere_autorisation='';
	$est_sejour_contigu=true;//s'il n'y a qu'un sejour, il y a contiguite
	$num_dernier_sejour_liste='';
	if($row_rs_ind['autrelieu']=='')
	{ $query_rs=" select codelieu from zrr where codelieu=".GetSQLValueString($row_rs_ind['codelieu'], "text")." and codelieu<>''";
		$rs=mysql_query($query_rs) or die(mysql_error()); 
		if($row_rs=mysql_fetch_assoc($rs))
		{ 
	if($row_rs_ind['datefin_sejour_prevu']=='')
	{ $plus_de_5_jours=true;
	}
	else
	{ $tab_duree_sejour=duree_aaaammjj($row_rs_ind['datedeb_sejour_prevu'], $row_rs_ind['datefin_sejour_prevu']);
		if($tab_duree_sejour['a']>0 || $tab_duree_sejour['m']>0 || $tab_duree_sejour['j']>5)
		{ $plus_de_5_jours=true;
		}
		else
		{ $pourquoi_pas_de_demande_fsd='- de 5j';
			$demander_autorisation=false;
		}
	}
	if($plus_de_5_jours)// sejour de plus de 5 j
	{ $derniere_autorisation_moins_de_5_ans=false;
		//$demander_autorisation=true;
		//$tab_dates_individu_sejours=$tab_dates_sejour[$codeindividu];
		// date de la derniere autorisation avant le sejour traite : les sejours sont listes dans l'ordre des date_deb_sejour croissants
		$fin=false;
		while(!$fin)
		{ if(list($un_numsejour_tab_dates_individu_sejours,$un_tab_dates_individu_sejours)=each($tab_dates_individu_sejours))
			{ if($un_tab_dates_individu_sejours['datefin_sejour']<$row_rs_ind['datedeb_sejour_prevu'] && $un_tab_dates_individu_sejours['datefin_sejour']!='')
				{ if($un_tab_dates_individu_sejours['date_autorisation']>=$date_derniere_autorisation)
					{ $date_derniere_autorisation=$un_tab_dates_individu_sejours['date_autorisation'];
						$num_sejour_derniere_autorisation=$un_numsejour_tab_dates_individu_sejours;
						$datefin_sejour_prec=$un_tab_dates_individu_sejours['datefin_sejour'];
						//echo $num_sejour_derniere_autorisation.' '.$date_derniere_autorisation.' '.$datefin_sejour_prec.'<br>';
					}
				}
				else
				{ $fin=true;// on est dans le sejour traite et/ou un sejour non ferme
				}
			}
			else
			{ $fin=true;// fin de liste
			}
		}
		if($date_derniere_autorisation=='')// en creation ou si pas d'autorisation anterieure
		{	$demander_autorisation=true;
			$pourquoi_demande_fsd='pas de date derniere autorisation';
		}
		else// contiguite des sejours entre celui de l'autorisation et le sejour traite
		{	// on est sur le sejour suivant celui de la date d'autorisation
			$fin=false;
			//reset($tab_dates_individu_sejours);
			while(!$fin && $est_sejour_contigu && !$demander_autorisation && ($un_tab_dates_individu_sejours['datefin_sejour']<$row_rs_ind['datedeb_sejour_prevu'] && $un_tab_dates_individu_sejours['datefin_sejour']!=''))
			{ $num_dernier_sejour_liste=$un_numsejour_tab_dates_individu_sejours;
				if($un_numsejour_tab_dates_individu_sejours==$row_rs_ind['numsejour'])
				{ $datedeb_sejour=$row_rs_ind['datedeb_sejour_prevu'];
					$datefin_sejour=$row_rs_ind['datefin_sejour_prevu'];
				}
				else
				{ $datedeb_sejour=$un_tab_dates_individu_sejours['datedeb_sejour'];
					$datefin_sejour=$un_tab_dates_individu_sejours['datefin_sejour'];
				}
				$est_sejour_contigu=$est_sejour_contigu && ($datedeb_sejour==date("Y/m/d",mktime(0,0,0,substr($datefin_sejour_prec,5,2),substr($datefin_sejour_prec,8,2)+1,substr($datefin_sejour_prec,0,4))));
				//echo '<br>'.$datefin_sejour_prec.($est_sejour_contigu?' contigu ':'non contigu').$datedeb_sejour;
				$datefin_sejour_prec=$datefin_sejour;
				if(!list($un_numsejour_tab_dates_individu_sejours,$un_tab_dates_individu_sejours)=each($tab_dates_individu_sejours))
				{ $fin=true;
				}
			}
			//echo $est_sejour_contigu;
			if($datefin_sejour_prec!='' && $num_dernier_sejour_liste!=$row_rs_ind['numsejour'])
			{ $est_sejour_contigu=$est_sejour_contigu && ($row_rs_ind['datedeb_sejour_prevu']==date("Y/m/d",mktime(0,0,0,substr($datefin_sejour_prec,5,2),substr($datefin_sejour_prec,8,2)+1,substr($datefin_sejour_prec,0,4))));
			//echo 'ici';
			}
			if($date_derniere_autorisation!='' && $row_rs_ind['datedeb_sejour_prevu']!='')
			{ $tab_duree_depuis_derniere_autorisation=duree_aaaammjj($date_derniere_autorisation, $row_rs_ind['datedeb_sejour_prevu']);
				if($tab_duree_depuis_derniere_autorisation['a']<5)
				{ $derniere_autorisation_moins_de_5_ans=true;
				}
			}
			if($derniere_autorisation_moins_de_5_ans && $est_sejour_contigu)
			{ $demander_autorisation=false;
				$pourquoi_pas_de_demande_fsd='FSD - de 5 ans';
			}
			else
			{ $demander_autorisation=true;
				$pourquoi_demande_fsd=$derniere_autorisation_moins_de_5_ans?'':'FSD + de 5 ans';
				$pourquoi_demande_fsd.=$est_sejour_contigu?'':' sejours non contigus';
			}
		}
	}
		}
	}
	return array('demander_autorisation'=>$demander_autorisation,'pourquoi_pas_de_demande_fsd'=>$pourquoi_pas_de_demande_fsd,'pourquoi_demande_fsd'=>$pourquoi_demande_fsd);
}

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

function rep_estvide($rep)
{ $estvide=true;
	if($handle = opendir($rep)) 
	{ while (($file = readdir($handle))!==false && $estvide) 
		{ $estvide=($file=='.' || $file=='..');//le while s'arrete au premier fichier ou rep hors . et ..
    }
    closedir($handle);
	}
	return $estvide;
}

function suppr_rep($rep)
{ clearstatcache();
	if(is_dir($rep))//si rep existe
	{ rmdir($rep);
	}
}

// construit le libelle d'une source ACI - Nom P. - RSA -- LDDIR
function construitlibsource($tab_construitsource)
{	$lib="";
	if(isset($tab_construitsource['codetypesource']) && $tab_construitsource['codetypesource']!='')
	{ $lib.=$tab_construitsource['libtypesource'];
	}
	if(isset($tab_construitsource['libsource']) && $tab_construitsource['libsource']!='')
	{ $lib.=($lib==""?'':' - ').$tab_construitsource['libsource'];
	}
	if(isset($tab_construitsource['coderespscientifique']) && $tab_construitsource['coderespscientifique']!='')
	{ $lib.=($lib==""?'':' - ').$tab_construitsource['nomrespscientifique'].' '.substr($tab_construitsource['prenomrespscientifique'],0,1).'.';
	}
	if(isset($tab_construitsource['codetypecredit']) && $tab_construitsource['codetypecredit']=='02'&& isset($tab_construitsource['libcentrecout_reel']) && $tab_construitsource['libcentrecout_reel']!='')
	{ $lib.=($lib==""?'':' - ').$tab_construitsource['libcentrecout_reel'];
	}
	return $lib;
}

function upload_file($fichiers,$rep_upload,$nom_tab_input_file,$key,$codetypepj)
{	// $key clé du tableau pj de $fichiers =codetypepj
  // traite tous les cas d'erreur lors du transfert mais ne peut pas traiter l'erreur du move_uploaded_file traitée à part
	// la doc indique que les navigateurs n'envoient pas tous max_file_size : les verifs sont faites apres la detection de $code_erreur
	$tab_res_upload=array('erreur'=>'','nomfichier'=>'');
	//conversion extension en minuscules : le download ne se fait pas correctement si extension en maj !!!
	$tab_decompose_nomfichier=explode('.', $fichiers[$nom_tab_input_file]['name'][$key]);
	end($tab_decompose_nomfichier);
	$tab_decompose_nomfichier[key($tab_decompose_nomfichier)]=strtolower(current($tab_decompose_nomfichier));
	$tab_res_upload['nomfichier']=implode('.',$tab_decompose_nomfichier);
	$extension = strtolower(end($tab_decompose_nomfichier));
	$codeerreur=$fichiers[$nom_tab_input_file]['error'][$key];
	if($codeerreur!=UPLOAD_ERR_OK && $codeerreur!=UPLOAD_ERR_NO_FILE)//pas d'erreur si OK ou pas de fichier
	{ $tab_res_upload['erreur']=$GLOBALS['tab_erreur_upload'][$codeerreur];
	}
	if($codeerreur==UPLOAD_ERR_OK)//pas de traitement pour UPLOAD_ERR_NO_FILE = pas de fichier
	{	//teste a nouveau les erreurs possibles car la doc indique que les navigateurs n'envoient pas tous les parametres (max_size_file).
		if(in_array($extension, $GLOBALS['file_types_array'])) 
		{ if($fichiers[$nom_tab_input_file]['size'][$key]<=$GLOBALS['max_file_size'])
			{ if(move_uploaded_file($fichiers[$nom_tab_input_file]['tmp_name'][$key],$rep_upload.'/'.$codetypepj))
				{ $codeerreur='';
				}
				else
				{ $tab_res_upload['erreur']='Une erreur est survenue lors du transfert.';
				}
			}
			else
			{ $tab_res_upload['erreur']=$GLOBALS['tab_erreur_upload'][UPLOAD_ERR_FORM_SIZE];
			}
		}
		else
		{ $tab_res_upload['erreur']=$GLOBALS['tab_erreur_upload'][UPLOAD_ERR_EXTENSION];
		}
	}
	if($tab_res_upload['erreur']!='')
	{ $tab_res_upload['erreur']=$tab_res_upload['nomfichier'].' non enregistr&eacute; : '.$tab_res_upload['erreur'];
	}
	return $tab_res_upload;
}

// affiche ligne : icone download+nom pj, remplacer par champ file, Effacer si editable=true
//$codeindividu,$codelibcatpj ('sejour' ou 'emploi'),$numcatpj (numero dans la categorie de pj) : cle individupj ('00001','sejour','01')
//$codelibtypepj : index unique de pjindividu ('cv') pour un couple  (codelibcatpj, codetypepj) cle de typepjindividu
//$txt_pj : texte a afficher comme nom de lien ou devant la zone de téléchargement
//$nom_form : nom du formulaire pour script js
//$editable : pj supprimable/telechargeable ou non
function ligne_txt_upload_pj_individu($codeindividu,$codelibcatpj,$numcatpj,$codelibtypepj,$txt_pj,$nom_form,$editable)
{ $contenu='';
	$rs=mysql_query("select codetypepj from typepjindividu where codelibcatpj=".GetSQLValueString($codelibcatpj, "text")." and codelibtypepj=".GetSQLValueString($codelibtypepj, "text")) or die(mysql_error());
	$row_rs=mysql_fetch_assoc($rs);  
	$codetypepj=$row_rs['codetypepj'];
	
	$rs=mysql_query("select individupj.* from individupj".
										" where codeindividu=".GetSQLValueString($codeindividu, "text").
										" and codelibcatpj=".GetSQLValueString($codelibcatpj, "text").
										" and numcatpj=".GetSQLValueString($numcatpj, "text").
										" and codetypepj=".GetSQLValueString($codetypepj, "text")) or die(mysql_error());
	if($row_rs=mysql_fetch_assoc($rs))
  { $contenu=	'<a href="download.php?codeindividu='.$codeindividu.'&codelibcatpj='.$codelibcatpj.'&numcatpj='.$numcatpj.'&codetypepj='.$codetypepj.'" target="_blank" title="T&eacute;l&eacute;charger '.$row_rs['nomfichier'].' ('.$txt_pj.')">'.
                                  '<img src="images/b_download.png" border="0">&nbsp;<span class="vertgrascalibri10">'.$txt_pj.'</span></a>';
		if($editable)															
    { $contenu.='&nbsp;&nbsp;<input type="image" name="submit_supprimer_une_pj#'.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.'##" class="icon" src="images/b_drop.png" title="Supprimer '.$txt_pj.'" onClick="return confirm(\'Supprimer : '.$txt_pj.'\')">'.
                '&nbsp;&nbsp;<span style="color:#FF9900; font-family:Calibri; font-size:10pt; font-weight:bold">remplacer par :&nbsp;</span><input type="file" name="pj['.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.']" class="noircalibri9" id="pj['.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.']"/>';
		}
  }
  else
  { if($editable)
		{ $contenu.='<span class="bleugrascalibri10">'.$txt_pj.' :&nbsp;</span><input type="file" name="pj['.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.']" class="noircalibri9" id="pj['.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.']">';
		}
  }
	if($editable)
	{ $liste_file_types=implode(", ",$GLOBALS['file_types_array']);
		$contenu.='&nbsp;<img src="images/b_info.png" border="0" width="16" height="16" id="sprytrigger_info_pj['.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.']">'.
            '<div class="tooltipContent_cadre" id="info_pj['.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.']">'.
            '<span class="noircalibri10">Le volume de tous les fichiers joints pour un dossier personnel est limit&eacute; &agrave; '.$GLOBALS['max_file_size_Mo'].'Mo'.
						' et doivent porter l&rsquo;une des extensions suivantes : <br>'.$liste_file_types.' (les extensions sont automatiquement transform&eacute;es en minuscules)<br>'.
						'La zone contenant le nom du fichier ne peut &ecirc;tre effac&eacute;e (uniquement modifi&eacute;e avec un autre fichier).<br>'.
						'Si un fichier a &eacute;t&eacute; s&eacute;lectionn&eacute; par erreur, la seule solution consiste &agrave; envoyer le formulaire qui retourne :<br>'.
						'- <img src="images/b_download.png" align="absbottom" border="0" width="16 height="16"> suivi du nom du fichier qui est t&eacute;l&eacute;chargeable ;<br>'.
						'- <img src="images/b_drop.png" border="0" align="absbottom" width="16 height="16"> pour supprimer le fichier (en cas d&rsquo;erreur notamment) ;<br>'.
						'</span>'.
						'- <span style="color:#FF9900; font-family:Calibri; font-size:10pt; font-weight:bold">remplacer par :&nbsp;</span>'.
						'<span class="noircalibri10">s&eacute;lectionner un nouveau fichier qui &eacute;crasera l&rsquo;ancien.<br>'.
						'Si, de plus, un message d&rsquo;erreur est affich&eacute; lors de l&rsquo;envoi du fichier, il faudra choisir un autre fichier ne provoquant pas<br>'.
						'cette erreur, l&rsquo;envoyer puis le supprimer...'.
						'</span></div>'.
            '<script type="text/javascript">'.
            'var sprytooltip_info_pj_'.$codelibcatpj.'_'.$numcatpj.'_'.$codelibtypepj.' = new Spry.Widget.Tooltip("info_pj['.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.']", "#sprytrigger_info_pj['.$codelibcatpj.'_'.$numcatpj.'_'.$codetypepj.']", {offsetX:20, offsetY:20});'.
            '</script>';
	}
	if(isset($rs)) {mysql_free_result($rs);}
	return $contenu;
}

function ligne_txt_upload_pj_contrat($codecontrat,$codelibtypepj,$txt_pj,$nom_form,$editable)
{ $contenu='';
	$rs=mysql_query("select codetypepj from typepjcontrat where codelibtypepj=".GetSQLValueString($codelibtypepj, "text")) or die(mysql_error());
	$row_rs=mysql_fetch_assoc($rs);  
	$codetypepj=$row_rs['codetypepj'];
	
	$rs=mysql_query("select contratpj.* from contratpj".
										" where codecontrat=".GetSQLValueString($codecontrat, "text").
										" and codetypepj=".GetSQLValueString($codetypepj, "text")) or die(mysql_error());
	if($row_rs=mysql_fetch_assoc($rs))
  { $contenu=	'<a href="download.php?codecontrat='.$codecontrat.'&codetypepj='.$codetypepj.'" target="_blank" title="T&eacute;l&eacute;charger '.$row_rs['nomfichier'].' ('.$txt_pj.')">'.
                                  '<img src="images/b_download.png" border="0">&nbsp;<span class="vertgrascalibri10">'.$txt_pj.'</span></a>';
		if($editable)															
    { $contenu.='&nbsp;&nbsp;<input type="image" name="submit_supprimer_une_pj#'.$codetypepj.'##" class="icon" src="images/b_drop.png" title="Supprimer '.$txt_pj.'" onClick="return confirm(\'Supprimer : '.$txt_pj.'\')">'.
                '&nbsp;&nbsp;<span style="color:#FF9900; font-family:Calibri; font-size:10pt; font-weight:bold">remplacer par :&nbsp;</span><input type="file" name="pj['.$codetypepj.']" class="noircalibri9" id="pj['.$codetypepj.']"/>';
		}
  }
  else
  { if($editable)
		{ $contenu.='<span class="bleugrascalibri10">'.$txt_pj.' :&nbsp;</span><input type="file" name="pj['.$codetypepj.']" class="noircalibri9" id="pj['.$codetypepj.']">';
		}
  }
	if($editable)
	{ $contenu.=ligne_txt_upload_pj_info($codetypepj,$codelibtypepj);
	}
	if(isset($rs)) {mysql_free_result($rs);}
	return $contenu;
}

function ligne_txt_upload_pj_projet($codeprojet,$codelibtypepj,$txt_pj,$nom_form,$editable)
{ $contenu='';
	$rs=mysql_query("select codetypepj from typepjprojet where codelibtypepj=".GetSQLValueString($codelibtypepj, "text")) or die(mysql_error());
	$row_rs=mysql_fetch_assoc($rs);  
	$codetypepj=$row_rs['codetypepj'];
	
	$rs=mysql_query("select projetpj.* from projetpj".
									" where codeprojet=".GetSQLValueString($codeprojet, "text").
									" and codetypepj=".GetSQLValueString($codetypepj, "text")) or die(mysql_error());
	if($row_rs=mysql_fetch_assoc($rs))
  { $contenu=	'<a href="download.php?codeprojet='.$codeprojet.'&codetypepj='.$codetypepj.'" target="_blank" title="T&eacute;l&eacute;charger '.$row_rs['nomfichier'].' ('.$txt_pj.')">'.
                                  '<img src="images/b_download.png" border="0">&nbsp;<span class="vertgrascalibri10">'.$txt_pj.'</span></a>';
		if($editable)															
    { $contenu.='&nbsp;&nbsp;<input type="image" name="submit_supprimer_une_pj#'.$codetypepj.'##" class="icon" src="images/b_drop.png" title="Supprimer '.$txt_pj.'" onClick="return confirm(\'Supprimer : '.$txt_pj.'\')">'.
                '&nbsp;&nbsp;<span style="color:#FF9900; font-family:Calibri; font-size:10pt; font-weight:bold">remplacer par :&nbsp;</span><input type="file" name="pj['.$codetypepj.']" class="noircalibri9" id="pj['.$codetypepj.']"/>';
		}
  }
  else
  { if($editable)
		{ $contenu.='<span class="bleugrascalibri10">'.$txt_pj.' :&nbsp;</span><input type="file" name="pj['.$codetypepj.']" class="noircalibri9" id="pj['.$codetypepj.']">';
		}
  }
	if($editable)
	{ $contenu.=ligne_txt_upload_pj_info($codetypepj,$codelibtypepj);
	}
	if(isset($rs)) {mysql_free_result($rs);}
	return $contenu;
}


function ligne_txt_upload_pj_commande($codecommande,$codelibtypepj,$txt_pj,$nom_form,$editable)
{ $contenu='';
	$rs=mysql_query("select codetypepj from typepjcommande where codelibtypepj=".GetSQLValueString($codelibtypepj, "text")) or die(mysql_error());
	$row_rs=mysql_fetch_assoc($rs);  
	$codetypepj=$row_rs['codetypepj'];
	
	$rs=mysql_query("select commandepj.* from commandepj".
										" where codecommande=".GetSQLValueString($codecommande, "text").
										" and codetypepj=".GetSQLValueString($codetypepj, "text")) or die(mysql_error());
	if($row_rs=mysql_fetch_assoc($rs))
  { $contenu=	'<a href="download.php?codecommande='.$codecommande.'&codetypepj='.$codetypepj.'" target="_blank" title="T&eacute;l&eacute;charger '.$row_rs['nomfichier'].' ('.$txt_pj.')">'.
                                  '<img src="images/b_download.png" border="0">&nbsp;<span class="vertgrascalibri10">'.$txt_pj.'</span></a>';
		if($editable)															
    { $contenu.='&nbsp;&nbsp;<input type="image" name="submit_supprimer_une_pj#'.$codetypepj.'##" class="icon" src="images/b_drop.png" title="Supprimer '.$txt_pj.'" onClick="return confirm(\'Supprimer : '.$txt_pj.'\')">'.
                '&nbsp;&nbsp;<span style="color:#FF9900; font-family:Calibri; font-size:10pt; font-weight:bold">remplacer par :&nbsp;</span><input type="file" name="pj['.$codetypepj.']" class="noircalibri9" id="pj['.$codetypepj.']"/>';
		}
  }
  else
  { if($editable)
		{ $contenu.='<span class="bleugrascalibri10">'.$txt_pj.' :&nbsp;</span><input type="file" name="pj['.$codetypepj.']" class="noircalibri9" id="pj['.$codetypepj.']">';
		}
  }
	if($editable)
	{ $contenu.=ligne_txt_upload_pj_info($codetypepj,$codelibtypepj);
	}
	if(isset($rs)) {mysql_free_result($rs);}
	return $contenu;
}

function ligne_txt_upload_pj_mission($codemission,$codelibtypepj,$txt_pj,$nom_form,$editable)
{ $contenu='';
	$rs=mysql_query("select codetypepj from typepjmission where codelibtypepj=".GetSQLValueString($codelibtypepj, "text")) or die(mysql_error());
	$row_rs=mysql_fetch_assoc($rs);  
	$codetypepj=$row_rs['codetypepj'];
	
	$rs=mysql_query("select missionpj.* from missionpj".
										" where codemission=".GetSQLValueString($codemission, "text").
										" and codetypepj=".GetSQLValueString($codetypepj, "text")) or die(mysql_error());
	if($row_rs=mysql_fetch_assoc($rs))
  { $contenu=	'<a href="download.php?codemission='.$codemission.'&codetypepj='.$codetypepj.'" target="_blank" title="T&eacute;l&eacute;charger '.$row_rs['nomfichier'].' ('.$txt_pj.')">'.
                                  '<img src="images/b_download.png" border="0">&nbsp;<span class="vertgrascalibri10">'.$txt_pj.'</span></a>';
		if($editable)															
    { $contenu.='&nbsp;&nbsp;<input type="image" name="submit_supprimer_une_pj#'.$codetypepj.'##" class="icon" src="images/b_drop.png" title="Supprimer '.$txt_pj.'" onClick="return confirm(\'Supprimer : '.$txt_pj.'\')">'.
                '&nbsp;&nbsp;<span style="color:#FF9900; font-family:Calibri; font-size:10pt; font-weight:bold">remplacer par :&nbsp;</span><input type="file" name="pj['.$codetypepj.']" class="noircalibri9" id="pj['.$codetypepj.']"/>';
		}
  }
  else
  { if($editable)
		{ $contenu.='<span class="bleugrascalibri10">'.$txt_pj.' :&nbsp;</span><input type="file" name="pj['.$codetypepj.']" class="noircalibri9" id="pj['.$codetypepj.']">';
		}
  }
	if($editable)
	{ $contenu.=ligne_txt_upload_pj_info($codetypepj,$codelibtypepj);
	}
	if(isset($rs)) {mysql_free_result($rs);}
	return $contenu;
}

function ligne_txt_upload_pj_info($codetypepj,$codelibtypepj)
{ $liste_file_types=implode(", ",$GLOBALS['file_types_array']);
	$txt_upload_pj_info='&nbsp;<img src="images/b_info.png" border="0" width="16" height="16" id="sprytrigger_info_pj['.$codetypepj.']">'.
					'<div class="tooltipContent_cadre" id="info_pj['.$codetypepj.']">'.
					'<span class="noircalibri10">Les fichiers accept&eacute;s sont limit&eacute;s &agrave; '.$GLOBALS['max_file_size_Mo'].'Mo'.
					' et doivent porter l&rsquo;une des extensions suivantes : <br>'.$liste_file_types.' (les extensions sont automatiquement transform&eacute;es en minuscules)<br>'.
					'La zone contenant le nom du fichier ne peut &ecirc;tre effac&eacute;e (uniquement modifi&eacute;e avec un autre fichier).<br>'.
					'Si un fichier a &eacute;t&eacute; s&eacute;lectionn&eacute; par erreur, la seule solution consiste &agrave; envoyer le formulaire qui retourne :<br>'.
					'- <img src="images/b_download.png" align="absbottom" border="0" width="16 height="16"> suivi du nom du fichier qui est t&eacute;l&eacute;chargeable ;<br>'.
					'- <img src="images/b_drop.png" border="0" align="absbottom" width="16 height="16"> pour supprimer le fichier (en cas d&rsquo;erreur notamment) ;<br>'.
					'</span>'.
					'- <span style="color:#FF9900; font-family:Calibri; font-size:10pt; font-weight:bold">remplacer par :&nbsp;</span>'.
					'<span class="noircalibri10">s&eacute;lectionner un nouveau fichier qui &eacute;crasera l&rsquo;ancien.<br>'.
					'Si, de plus, un message d&rsquo;erreur est affich&eacute; lors de l&rsquo;envoi du fichier, il faudra choisir un autre fichier ne provoquant pas<br>'.
					'cette erreur, l&rsquo;envoyer puis le supprimer...'.
					'</span></div>'.
					'<script type="text/javascript">'.
					'var sprytooltip_info_pj_'.$codelibtypepj.' = new Spry.Widget.Tooltip("info_pj['.$codetypepj.']", "#sprytrigger_info_pj['.$codetypepj.']", {offsetX:20, offsetY:20});'.
					'</script>';
	return $txt_upload_pj_info;
}


// dernier visa (role) apposé
function max_individustatutvisa($codeindividu,$numsejour)
{	$query_individustatutvisa=("select codestatutvisa,coderole".
															" from statutvisa ".
															" where codestatutvisa in (select max(codestatutvisa) from individustatutvisa where codeindividu=".GetSQLValueString($codeindividu, "text")." and numsejour=".GetSQLValueString($numsejour, "text").")");
	$rs_individustatutvisa=mysql_query($query_individustatutvisa) or die(mysql_error());
	if(!($row_rs_individustatutvisa=mysql_fetch_assoc($rs_individustatutvisa)))//max de codestatutvisa ou '' si existe pas
	{ $row_rs_individustatutvisa['codestatutvisa']='';
		$row_rs_individustatutvisa['coderole']='';
	}
	
	if(isset($rs_individustatutvisa))mysql_free_result($rs_individustatutvisa);
	return $row_rs_individustatutvisa;
}

// renvoie $tab_statutvisa=liste de tous les statutvisa existants(roles)  sous la forme ('referent'=>'01', 'srhue'=>'02', ... ,'du'=>'05',....'gestul'=>'09')
function get_statutvisa()
{ $tab_statutvisa=array();
  $rs_statutvisa=mysql_query("select codestatutvisa,coderole from statutvisa where codestatutvisa<>'' order by codestatutvisa") or die(mysql_error());
  while($row_rs_statutvisa = mysql_fetch_assoc($rs_statutvisa))
  { $tab_statutvisa[$row_rs_statutvisa['coderole']]=$row_rs_statutvisa['codestatutvisa']; 
  }
  mysql_free_result($rs_statutvisa);  
  return $tab_statutvisa;
}

//------------------ ROLES : $codeuser a un ou plusieurs roles ($tab_roleuser) dans la liste de tous les roles ($tab_statutvisa)
// utilise pour :
// - role de façon générale (codeindividu ='', numsejour ='')
// - role pour un (codeindividu,numsejour)
function get_tab_roleuser($codeuser,$codeindividu,$numsejour,$tab_statutvisa,$estreferent,$estresptheme)
{ // renvoie table $tab_result['tab_roleuser']=$tab_roleuser = array('referent'=>'01') par ex.
	//               $tab_result['estreferent']=$estreferent
	//               $tab_result['estresptheme']=$estresptheme;
	// $tab_roleuser contient la liste des roles d'un individu : referent, resptheme, du pour le directeur, encadrant de these et resp. de gt par ex.
	$tab_result=array();
	$tab_roleuser=array();// table des roles
	//$estreptheme=false;
  //role referent : pour un individu précis. Référent ne peut pas etre attribue pour la liste des individus
  if($codeindividu!='')
	{ $rs_individu=mysql_query("select codereferent,codegesttheme,codecreateur,codemodifieur".
		  				 							" from individusejour where codeindividu=".GetSQLValueString($codeindividu, "text").
														" and numsejour=".GetSQLValueString($numsejour, "text")) or die(mysql_error());
		$row_rs_individu = mysql_fetch_assoc($rs_individu);
		if($codeuser==$row_rs_individu['codereferent'] || $codeuser==$row_rs_individu['codegesttheme'] || $codeuser==$row_rs_individu['codecreateur'] || $codeuser==$row_rs_individu['codemodifieur'])
		{ $tab_roleuser['referent']=$tab_statutvisa['referent'];//le role referent est donne a la personne qui valide cette saisie
		}
		$estreferent=($codeuser==$row_rs_individu['codereferent']);
	}

  // role theme non resp. en tant que gesttheme de façon generale si $codeindividu='' et numsejour='', sinon pour l'individu $codeindividu
  $query_rs_gestthemeindividu="select * from individutheme,gesttheme,structure".
															" where individutheme.codetheme=gesttheme.codetheme ".
															" and gesttheme.codetheme=structure.codestructure".
															($codeindividu==""?"":" and individutheme.codeindividu = ".GetSQLValueString($codeindividu, "text")).
															($numsejour==""?"":" and individutheme.numsejour = ".GetSQLValueString($numsejour, "text")).									
															" and gesttheme.codegesttheme = ".GetSQLValueString($codeuser, "text");
  $rs_gestthemeindividu=mysql_query($query_rs_gestthemeindividu);
  $nb_rs_gestthemeindividu = mysql_num_rows($rs_gestthemeindividu);
  if($nb_rs_gestthemeindividu!=0)// gest theme
  { $tab_roleuser['theme']=$tab_statutvisa['theme'];
    $estresptheme=false;//correction orthographe estreptheme le 30/01/2012
  }

  // role theme si resp. en tant que resptheme de façon generale si $codeindividu='' et numsejour='', sinon pour l'individu $codeindividu de $numsejour
  $query_rs_respthemeindividu="select * from individutheme,structureindividu".
															" where individutheme.codetheme=structureindividu.codestructure ".
															($codeindividu==""?"":" and individutheme.codeindividu = ".GetSQLValueString($codeindividu, "text")).
															($numsejour==""?"":" and individutheme.numsejour = ".GetSQLValueString($numsejour, "text")).									
															" and structureindividu.codeindividu = ".GetSQLValueString($codeuser, "text");
  $rs_respthemeindividu=mysql_query($query_rs_respthemeindividu);
  $nb_rs_respthemeindividu = mysql_fetch_assoc($rs_respthemeindividu);
  if($nb_rs_respthemeindividu!=0)// resp de theme
  { $tab_roleuser['theme']=$tab_statutvisa['theme'];
    $estresptheme=true;
  }

  // roles du, sii, admingestfin, gestcnrs (provenant de) structure
  $rs_structureindividu=mysql_query("select codeindividu,codelib from structureindividu,structure".
																		" where structureindividu.codestructure=structure.codestructure".
																		" and (codelib=".GetSQLValueString('srh', "text")." or codelib=".GetSQLValueString('du', "text").
																		" 			or codelib=".GetSQLValueString('sii', "text")." or codelib=".GetSQLValueString('admingestfin', "text").
																		" or codelib=".GetSQLValueString('gestul', "text").
																		" or codelib=".GetSQLValueString('gestcnrs', "text").
																		" or codelib=".GetSQLValueString('gestperscontrat', "text").")") or die(mysql_error()); //and estresp='oui'
  while($row_rs_structureindividu = mysql_fetch_assoc($rs_structureindividu))
  { if($row_rs_structureindividu['codeindividu']==$codeuser)
    { $tab_roleuser[$row_rs_structureindividu['codelib']]=$tab_statutvisa[$row_rs_structureindividu['codelib']];
    }
  }
  // role srhue pour le role srh
  if(array_key_exists('srh',$tab_roleuser))
  { $tab_roleuser['srhue']=$tab_statutvisa['srhue'];
  }
  $tab_result['tab_roleuser']=$tab_roleuser;
  $tab_result['estreferent']=$estreferent;
  $tab_result['estresptheme']=$estresptheme;
  
  if(isset($rs_individu)) mysql_free_result($rs_individu);
  if(isset($rs_respthemeindividu)) mysql_free_result($rs_respthemeindividu);
  if(isset($rs_structureindividu)) mysql_free_result($rs_structureindividu);
  if(isset($rs_gestthemeindividu)) mysql_free_result($rs_gestthemeindividu);
  return $tab_result;
// ------------------ FIN des roles $codeuser
}

// get_info_user : informations du user connecte sous forme de tableau. Le user doit etre present
// 'codeindividu'=>codeindividu, 'nom'=> nom, 'prenom'=>prenom, 'email'=>email
// 'codetheme'=>array(codetheme1,codetheme2,...), theme=>liste lib courts séparés par virgules
function get_info_user($codeuser)
{ $tab_info_user=array();
  $rs_individu=mysql_query("select codeindividu, nom, prenom, email  from individu where codeindividu=".GetSQLValueString($codeuser, 'text'));
  if($row_rs_individu=mysql_fetch_assoc($rs_individu))
  { $tab_info_user['codeindividu']=$row_rs_individu['codeindividu'];
    $tab_info_user['nom']=$row_rs_individu['nom'];
    $tab_info_user['prenom']=$row_rs_individu['prenom'];
    $tab_info_user['email']=$row_rs_individu['email'];
  }
  // theme(s) pour un codeuser
	$query_individutheme= "SELECT individutheme.codetheme,libcourt_fr from individusejour,individutheme,structure".
												" WHERE individusejour.codeindividu=individutheme.codeindividu AND individusejour.numsejour=individutheme.numsejour".
												" AND individutheme.codetheme=structure.codestructure AND structure.esttheme='oui'".
												" AND ".periodeencours('datedeb_sejour','datefin_sejour')." AND ".periodeencours('datedeb_theme','datefin_theme').
												// debut modif historique theme 20121231
												" AND ".periodeencours('structure.date_deb','structure.date_fin').
												// fin modif historique theme 20121231
												" AND individutheme.codeindividu=".GetSQLValueString($codeuser, "text") or die(mysql_error());
  $rs_individutheme=mysql_query($query_individutheme);
  $tab_info_user['codetheme']=array();
	$tab_info_user['theme']="";//pas de theme par defaut
  $first=true;
  while($row_rs_individutheme = mysql_fetch_assoc($rs_individutheme))
  { $tab_info_user['codetheme'][]=$row_rs_individutheme['codetheme'];
	  if($first)
    { $tab_info_user['theme']=$row_rs_individutheme['libcourt_fr'];
	  	$first=false;
		}
		else
		{ $tab_info_user['theme'].=", ".$row_rs_individutheme['libcourt_fr'];
		}
  }
  //theme(s) pour un codeuser resptheme
  /*$rs_structureindividu=mysql_query("select libcourt_fr from structureindividu,structure".
																		" where structureindividu.codestructure=structure.codestructure ".
																		" and codeindividu=".GetSQLValueString($codeuser, 'text')) or die(mysql_error());
  while($row_rs_structureindividu = mysql_fetch_assoc($rs_structureindividu))
  { $tab_info_user['theme']=$row_rs_structureindividu['libcourt_fr'];
  }
  // theme(s) pour un codeuser gesttheme
  $rs_gesttheme=mysql_query("select libcourt_fr from gesttheme,structure".
									" where gesttheme.codetheme=structure.codestructure and codegesttheme=".GetSQLValueString($codeuser, 'text'));
  $first=true;
  while($row_rs_gesttheme = mysql_fetch_assoc($rs_gesttheme))
  { if($first)
    { $tab_info_user['theme']=$row_rs_gesttheme['libcourt_fr'];
	  $first=false;
		}
		else
		{ $tab_info_user['theme'].=", ".$row_rs_gesttheme['libcourt_fr'];
		}
  }*/
  if(isset($rs_individutheme)) mysql_free_result($rs_individutheme);  
  if(isset($rs_structureindividu)) mysql_free_result($rs_structureindividu);
  if(isset($rs_individu)) mysql_free_result($rs_individu);
  if(isset($rs_gesttheme)) mysql_free_result($rs_gesttheme);

  return $tab_info_user;
}

function tablehtml_info_user($tab_infouser,$tab_roleuser)
{	$tablehtml= 		
	'			<table border="0" cellspacing="1" cellpadding="0">
					<tr>
						<td><img src="images/b_individu.png" width="14" height="18">
						</td>
						<td>
							<span class="bleucalibri9">Utilisateur Connect&eacute;&nbsp;:&nbsp;</span>
							<span class="mauvegrascalibri9">'.$tab_infouser['prenom'].' '.$tab_infouser['nom'].'</span> <span class="mauvecalibri9">['.$tab_infouser['theme'].']&nbsp;</span>';
							/*if(!empty ($tab_roleuser))
							{ $tablehtml.= 		
	'						<span class="bleucalibri9">&nbsp;:</span>';
								asort ( $tab_roleuser );
								$first=true;
								foreach($tab_roleuser as $keyrole=>$valrole) 
								{ $tablehtml.= 
	'						<span class="mauvemajuscule">&nbsp;[&nbsp;'.($first?"":" &shy; ").($keyrole=="theme"?"GT&nbsp;:&nbsp;":$keyrole).
								($keyrole=="theme"?$tab_infouser['theme']:"").'&nbsp;]</span>'; 
								$first=false;
								} 
							}*/
							$tablehtml.=
'						</td>
					</tr>
				</table>';
	return $tablehtml;
}

function get_individu_visas($codeindividu,$numsejour,$tab_statutvisa)
{ //------------------ VISAS (roles) : $codeindividu a deja un ou plusieurs visas $tab_individustatutvisa apposes dans la liste de tous les visas (roles) $tab_statutvisa
  //liste des statutvisa deja apposes pour cet individu 
	// 'referent'=>01, srhue=>'02',...
  $tab_individustatutvisa=array();
  $query_rs_individustatutvisa="SELECT individustatutvisa.*,coderole from individustatutvisa,statutvisa".
															 " where individustatutvisa.codeindividu=".GetSQLValueString($codeindividu, "text").
															 " and individustatutvisa.numsejour=".GetSQLValueString($numsejour, "text").
															 " and individustatutvisa.codestatutvisa=statutvisa.codestatutvisa".
															 " order by individustatutvisa.codestatutvisa";
  $rs_individustatutvisa=mysql_query($query_rs_individustatutvisa) or die(mysql_error()); 
  while($row_rs_individustatutvisa = mysql_fetch_assoc($rs_individustatutvisa))
  { $tab_individustatutvisa[$row_rs_individustatutvisa['coderole']]=$tab_statutvisa[$row_rs_individustatutvisa['coderole']];
  }
  
  mysql_free_result($rs_individustatutvisa);
  return $tab_individustatutvisa;

}// ------------------ FIN des visas $codeindividu

// -------------------- Droits de modif des roles de codeuser et statut de visa pour la colonne concernee colstatutvisa
/* Retourne, pour un dossier individu, le droit read/write pour le role de la colonne concernee
   et pour la colonne de visa $colstatutvisa consideree l'etat a afficher (appose, a valider, en cours ou en attente)
	 pour le user de role $tab_roleuser  
*/
function contenu_col_role_droit($ue,$tab_individustatutvisa,$tab_roleuser,$colstatutvisa)
{ /* $ue : si $ue=non (horsue) la colonne srhue est concernee sinon n/a
    $tab_individustatutvisa = liste des visas deja apposes
	$tab_roleuser=liste des roles du user codeuser
	$colstatutvisa=colonne concernee 
  */
  $contenu="";//ne doit pas etre vide pour les colonnes de roles a afficher : mettre n/a s'il n'y a rien a mettre d'autre
  $droit="read";// valeur par defaut de droit (read/write) du role $role 
  if($colstatutvisa=='referent') 
  { // si visa 'referent' appose pour $codeindividu
		if(array_key_exists('referent',$tab_individustatutvisa))
		{ $contenu = "visa appose";
		} 
		else // le visa 'referent' n'est pas appose pour $codeindividu
		{ if(array_key_exists('referent',$tab_roleuser))// $codeuser a le role 'referent' meme si le referent r&eacute;el n'est pas lui
	  	{ $droit="write";	  
	    	$contenu = "valider";
	  	}
      else// $codeuser n'a pas le role 'referent'
	  	{ $contenu = "brancher";
	  	}
		}	
  }
  else if($colstatutvisa=='srhue')// visa 'visasrhue'
  { if($ue=='oui')// UE
		{ $contenu = "n/a";
    } 
		else// hors UE
		{ if(array_key_exists('srhue',$tab_individustatutvisa))// visa 'visasrhue' appose
      { $contenu = "visa appose";
	  	}
	  	else// visa 'visasrhue' non appose
	  	{ if(array_key_exists('referent',$tab_individustatutvisa))//visa referent appose
				{ if(array_key_exists('srhue',$tab_roleuser))// $codeuser a le role 'srhue'
      	 	{ $droit="write";
		    		$contenu = "valider";
		  		}	
        	else // $codeuser n'a pas le role 'srhue'
      		{ $contenu = "brancher";
		  		}
				}
				else//visa referent non appose : attente de visa referent
      	{ $contenu ="sablier";
				}
	  	}
		}
  }
  else if($colstatutvisa=='theme')// visa 'theme'
  {	if(array_key_exists('theme',$tab_individustatutvisa)) // visa 'theme' appose $codeindividu
		{ $contenu = "visa appose";
		} 
		else // visa 'theme' n'est pas appose pour $codeindividu
		{ if(array_key_exists('theme',$tab_roleuser))// UE ou visa 'srhue' et $codeuser a le role 'theme' 
			{ if(!array_key_exists('referent',$tab_individustatutvisa))//visa referent non appose
		  	{ $contenu = "sablier";
		  	}
		  	else //visa referent appose
		  	{ $droit="write";
		    	$contenu = "valider";
		  	}
	    }
      else // $codeuser n'a pas le role 'theme'
	    { if(!array_key_exists('referent',$tab_individustatutvisa))//visa referent non appose 
		  	{ $contenu = "sablier";
		  	}
        else
        { $contenu ="brancher";
		  	}
			}
	  }
  }
  $tab_contenu_col_role_droit[$colstatutvisa]['droit']=$droit;
  $tab_contenu_col_role_droit[$colstatutvisa]['colonne']=$contenu;
  return $tab_contenu_col_role_droit;
}

function get_tab_individu_acteurs($row_rs_individu)
{ $liste_acteurs=array();
  $tab_acteurs['referent'][1]=get_info_user($row_rs_individu['codereferent']);
	$tab_acteurs['gesttheme'][1]=get_info_user($row_rs_individu['codegesttheme']);

  // resptheme(s) pour cet individu sous la forme themeXX ou XX=codetheme
  $rs=mysql_query("select structure.libcourt_fr as libtheme, structureindividu.codeindividu as coderesptheme".
									" from individutheme,structureindividu,structure".
									" where individutheme.codetheme=structureindividu.codestructure".
									" and structureindividu.codestructure=structure.codestructure and structureindividu.estresp='oui'".
									" and individutheme.codeindividu=".GetSQLValueString($row_rs_individu['codeindividu'], 'text').
									" and individutheme.numsejour=".GetSQLValueString($row_rs_individu['numsejour'], 'text').
									" AND ".periodeencours('structure.date_deb','structure.date_fin')
									);
	$i=0;
  while($row_rs = mysql_fetch_assoc($rs))
  { $i++;
		$tab_acteurs['theme'][$i]=get_info_user($row_rs['coderesptheme']);
  }
  // roles du, srh, sii, admingestfin (provenant de) structure
  $rs=mysql_query("select codeindividu as coderesp,codelib from structureindividu,structure".
								    " where structureindividu.codestructure=structure.codestructure".
								    " and (codelib=".GetSQLValueString('srh', "text")." or codelib=".GetSQLValueString('du', "text")." or codelib=".GetSQLValueString('admingestfin', "text").
									  " or (codelib=".GetSQLValueString('sii', "text")." and structureindividu.estresp='oui'))") or die(mysql_error());
  $i=0;
	while($row_rs = mysql_fetch_assoc($rs))
  { $i++;
		$tab_acteurs[$row_rs['codelib']][$i]=get_info_user($row_rs['coderesp']);
  }
  // role srhue pour le role srh
  if(array_key_exists('srh',$tab_acteurs))
  { list($i,$tab)=each($tab_acteurs['srh']);
		$tab_acteurs['srhue'][1]=$tab_acteurs['srh'][$i];
  }
  if(isset($rs))mysql_free_result($rs);
  return $tab_acteurs;
}

function get_roles_liblong()
{ // libelles 'longs' des roles acteurs
	$tab_roles_liblong=array();
	$rs=mysql_query("select coderole, liblong from statutvisa where codestatutvisa<>'' order by codestatutvisa") or die(mysql_error());
  while($row_rs = mysql_fetch_assoc($rs))
  { $tab_roles_liblong[$row_rs['coderole']]=$row_rs['liblong']; 
  }
	$libtheme='D&eacute;pt';
	$libtheme=$GLOBALS['libcourt_theme_fr'];
	$tab_roles_liblong['gesttheme']='Gestionnaire '.$libtheme;  
	$tab_roles_liblong['theme']='Responsable '.$libtheme;
	$tab_roles_liblong['admingestfin']='Responsable Admin.';
	if(isset($rs))mysql_free_result($rs);
  return $tab_roles_liblong;

}

function sujet_saisi_valide($row_rs_individu,$codelibstatutvisa)
{	/* DOCTORANT, STAGIAIRE MASTER, STAGIAIRE A SUJET OBLIGATOIRE, EXTERIEUR avec demander_autorisation 
										 sujet saisi	? non			
																		oui	: theme
																					sujet_valide_par_theme	?	non			
																																		oui	srh, du 
	*/
	$sujet_obligatoire_saisi=($row_rs_individu['codesujet']!="");
	$sujet_valide_par_theme=($row_rs_individu['codestatutsujet']=='V' || $row_rs_individu['codestatutsujet']=='P');
	$valider_visa_possible=true;
	$texte_attente_sujet="";
	if($row_rs_individu['codelibcat']=='DOCTORANT' 
		|| ($row_rs_individu['codelibcat']=='STAGIAIRE' && ($row_rs_individu['codelibtypestage']=='MASTER' || ($row_rs_individu['codelibtypestage']!='MASTER' && $row_rs_individu['sujetstageobligatoire']=='oui'))) //&& $row_rs_individu['datedeb_sejour']>=$GLOBALS['date_zrr_obligatoire']
	  || ($row_rs_individu['codelibcat']=='EXTERIEUR' && $row_rs_individu['demander_autorisation'])) //&& $row_rs_individu['datedeb_sejour']>=$GLOBALS['date_zrr_obligatoire']
	{ //if($row_rs_individu['datedeb_sejour']>=$GLOBALS['date_zrr_obligatoire'])// ajout 14/09/2014
		{ if($sujet_obligatoire_saisi==false)
			{	if($codelibstatutvisa=='theme' || $codelibstatutvisa=='srh' || $codelibstatutvisa=='du')
				{ $valider_visa_possible=false;
				}
				$texte_attente_sujet="En attente de saisie du sujet par ";
				$tab_info_referent=get_info_user($row_rs_individu['codereferent']);
				$texte_attente_sujet.=$tab_info_referent['prenom'].' '.$tab_info_referent['nom'];
			}
			else
			{ if($sujet_valide_par_theme==false)
				{	if($codelibstatutvisa=='srh' || $codelibstatutvisa=='du')
					{ $valider_visa_possible=false;
					}
					$texte_attente_sujet="En attente de validation du sujet par le Responsable de ".$GLOBALS['libcourt_theme_fr'];
				}
			}
		}
	}
	return array('sujet_saisi_valide'=>$valider_visa_possible,'texte_attente_sujet'=>$texte_attente_sujet);
}

function popup_validation_individu($row_rs_individu,$codeuser,$tab_roleuser,$codevisa_a_apposer,$estresptheme,$estreferent)
{ /* destinataires de message : 
  'referent' : referent, gesttheme, resptheme, srhue si pas ue
	'srhue' : referent, gesttheme, resptheme1,...
	'theme' : referent, gesttheme, resptheme1,..., srh
	'srh' : gesttheme, resptheme1,..., du
	'du' : referent, gesttheme, resptheme1,..., srh
  */
  // le user codeuser n'est pas destinataire (&eacute;ventuel) du message envoy&eacute; a certains autres acteurs
	$destinataires='';
	$message='';
	$tab_acteurs=get_tab_individu_acteurs($row_rs_individu);
	$tab_destinataires=array();
	$tab_statutvisa=get_statutvisa();//referent=>01, srhu...tous les roles dont sii, adminfin,...
	$codevisa_a_apposer_lib=array_search($codevisa_a_apposer,$tab_statutvisa);
	$texte_visa_appose="";
	$tab_statutvisa['gesttheme']='';
	
  foreach($tab_acteurs as $coderoleacteur=>$tab_acteurs_par_role)
  { foreach($tab_acteurs_par_role as $ieme_acteur=>$tab_info_un_acteur_du_role)
		{ $un_destinataire=array('codeacteur'=>$tab_info_un_acteur_du_role['codeindividu'],'prenomnom'=>$tab_info_un_acteur_du_role['prenom'].' '.
																	$tab_info_un_acteur_du_role['nom'],
																'coderoleacteur'=>$coderoleacteur);
			if($codevisa_a_apposer_lib=='referent')
			{	if($coderoleacteur=='referent' || $coderoleacteur=='gesttheme' || $coderoleacteur=='theme' || ($coderoleacteur=='srhue' && $row_rs_individu['ue']=='non'))
				{ $tab_destinataires[]=$un_destinataire;
				}
			}
			else if($codevisa_a_apposer_lib=='srhue')
			{ if($coderoleacteur=='referent' || $coderoleacteur=='gesttheme' || $coderoleacteur=='theme')
				{ $tab_destinataires[]=$un_destinataire;
					//$tab_cpt_role[$coderoleacteur]++;
				}
			}
			else if($codevisa_a_apposer_lib=='theme')
			{ if($coderoleacteur=='referent' || $coderoleacteur=='gesttheme' || $coderoleacteur=='theme'/*  || $coderoleacteur=='srh' */)
				{ $tab_destinataires[]=$un_destinataire;
				}
			}
		}
	}
	// libelles longs des roles acteurs
	$tab_roles_liblong=get_roles_liblong();

	//suppression des doublons de noms de destinataires et une ligne par destinataire avec son ou ses roles en libelle long
	$tab_destinataire_roles=array();
	foreach($tab_destinataires as $un_destinataire)
	{ if(array_key_exists($un_destinataire['codeacteur'],$tab_destinataire_roles))
		{ $tab_destinataire_roles[$un_destinataire['codeacteur']].=', '.$tab_roles_liblong[$un_destinataire['coderoleacteur']];
		}
		else
		{ $tab_destinataire_roles[$un_destinataire['codeacteur']]='- '.$un_destinataire['prenomnom'].' : '.$tab_roles_liblong[$un_destinataire['coderoleacteur']];
		}
	}
	
  $message.=addslashes("Cette action appose le visa &laquo;".($codevisa_a_apposer_lib=='srhue'?'fsd':$codevisa_a_apposer_lib)."&raquo; au dossier de ".
					   $row_rs_individu['libciv_fr']." ".$row_rs_individu['prenom'].
					   " ".$row_rs_individu['nom'].".")."\\n";
	$message.="Un mail va &ecirc;tre envoy&eacute &agrave; :"."\\n";
	foreach($tab_destinataire_roles as $codeacteur=>$ligne_destinataire)
	{ $message.=addslashes($ligne_destinataire)."\\n";
	}
	if(isset($row_rs_individu['texte_attente_sujet']) && $row_rs_individu['texte_attente_sujet']!='')
	{ $message.="Le message pr&eacute;cisera : ".addslashes($row_rs_individu['texte_attente_sujet']);
	}
	if($codevisa_a_apposer_lib=='theme')
	{ $message.="\\n".addslashes("Suite &agrave; ce visa, un mail sera envoy&eacute; &agrave; cran_direction, ACMO et Service informatique dans un d&eacute;lai de 2 jours maximum")."\\n";
	}	
	
  if(isset($rs_individuaction))mysql_free_result($rs_individuaction);
  if(isset($rs))mysql_free_result($rs);
	return $message;
}

function message_action_individu($row_rs_individu,$codeuser,$tab_roleuser,$action)// action supprimer dossier, invalider
{ /* destinataires de message : 
  'referent' : referent, gesttheme, resptheme, srhue si pas ue
	'srhue' : referent, gesttheme, resptheme1,...
	'theme' : referent, gesttheme, resptheme1,..., srh
	'srh' : gesttheme, resptheme1,..., du
	'du' : referent, gesttheme, resptheme1,..., srh
  */
  // le user codeuser n'est pas destinataire (&eacute;ventuel) du message envoy&eacute; a certains autres acteurs
	$destinataires='';
	$message='';
	$tab_acteurs=get_tab_individu_acteurs($row_rs_individu);
	$tab_destinataires=array();
	$tab_coderole=array();
	$tab_statutvisa=get_statutvisa();//referent=>01, srhu...tous les roles dont sii, adminfin,...
	// libelles longs des roles acteurs
	$tab_roles_liblong=get_roles_liblong();

	$tab_individu_visas_apposes=get_individu_visas($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$tab_statutvisa);
	/* if(in_array($tab_statutvisa['du'],$tab_individu_visas_apposes) || in_array($tab_statutvisa['srh'],$tab_individu_visas_apposes))
	{ $tab_coderole=array('referent','theme','gesttheme','srh','du','admingestfin');
	}
	else  */
	if(in_array($tab_statutvisa['theme'],$tab_individu_visas_apposes))
	{ $tab_coderole=array('referent','theme','gesttheme'/* ,'srh' */);
	}
	else if(in_array($tab_statutvisa['referent'],$tab_individu_visas_apposes))
	{ $tab_coderole=array('referent','theme','gesttheme');
	}
	if(in_array($tab_statutvisa['referent'],$tab_individu_visas_apposes))//srhue a un message si au minimum visa referent
	{ $tab_coderole[]='srhue';
	}
	
	$tab_codeacteur=array();
	foreach($tab_coderole as $coderole)
	{ foreach($tab_acteurs as $coderoleacteur=>$tab_un_acteur)
		{ if($coderoleacteur==$coderole)
			{ foreach($tab_un_acteur as $i=>$tab_infouser)
				{ $codeacteur=$tab_infouser['codeindividu'];
					if(in_array($codeacteur,$tab_codeacteur))// pas de doublons dans les destinataires : plusieurs roles eventuels
					{ $tab_destinataire_roles[$codeacteur].=', '.$tab_roles_liblong[$coderoleacteur];
					}
					else
					{ $tab_codeacteur[]=$codeacteur;
						$tab_destinataire_roles[$codeacteur]='- '.$tab_infouser['prenom'].' '.$tab_infouser['nom'].' : '.$tab_roles_liblong[$coderoleacteur];
					}
				}
			}
		}
	}
	switch ($action)
	{	case "invalider" :
			$message.='<p align="center"><b>Cette action invalide tous les visas du dossier de '.
								 $row_rs_individu['libciv_fr']." ".$row_rs_individu['prenom'].
								 " ".$row_rs_individu['nom']." pour le s&eacute;jour concern&eacute;.</b>"."</p>";
			$message.="La proc&eacute;dure d&rsquo;accueil devra, le cas &eacute;ch&eacute;ant, &ecirc;tre enti&egrave;rement r&eacute;appliqu&eacute;e."."<br>";
			break;
		case "supprimer" :
			$supprindividu=false;
			$rs=mysql_query("select * from individusejour  where codeindividu=".GetSQLValueString($row_rs_individu['codeindividu'], "text")) or die(mysql_error());
			if(mysql_num_rows($rs)==1)// un seul sejour : suppression de l'individu et du séjour si $supprsejour
			{ $supprindividu=true;
			}
			$message.='<p align="center"><b>Cette action supprime '.($supprindividu?"le dossier":"le s&eacute;jour")." de ".
								 $row_rs_individu['libciv_fr']." ".$row_rs_individu['prenom'].
								 " ".$row_rs_individu['nom']."</b>"."</p>";
			mysql_free_result($rs);
			break;
		//debut modif visa fsd
		case "valider" :
			$message.=str_replace("\\n","<br>",popup_validation_individu($row_rs_individu,$codeuser,$tab_roleuser,'02',false,false));
			break;
		//fin modif visa fsd
		default :
			break;
	}
	if(!empty($tab_destinataire_roles) && $action!="valider")
	{ $message.="Un mail sera envoy&eacute aux acteurs concern&eacute;s par ce dossier &agrave; ce stade de la proc&eacute;dure :"."<br>";
		foreach($tab_destinataire_roles as $une_ligne_destinataire)
		{ $message.=$une_ligne_destinataire."<br>";
		}
	}
	return $message;
}

function mail_adminbd($level,$programme,$message)
{ $subject=html_entity_decode($level.' '.$programme);
	$html_message=html_entity_decode($message);
	$from = $GLOBALS['Serveur12+']['nom'].'<'.$GLOBALS['Serveur12+']['email'].'>';
	$to=$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	$replyto=$to;
	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto,'Subject' => $subject);
	$mime = new Mail_mime("\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);

	$headers = $mime->headers($headers);
	
	$erreur=""; 
	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message_html_txt);//envoimail($tab_destinataires, $headers, $message);
	}
	else
	{ $erreur=$message;
	}
	return;	
}
function mail_action_individu($row_rs_individu,$codeuser,$action)
{ /* destinataires de message : 
  'referent' : referent, gesttheme, resptheme, srhue si pas ue
	'srhue' : referent, gesttheme, resptheme1,...
	'theme' : referent, gesttheme, resptheme1,..., srh
	'srh' : gesttheme, resptheme1,..., du
	'du' : referent, gesttheme, resptheme1,..., srh
  */
  // le user codeuser n'est pas destinataire (&eacute;ventuel) du message envoy&eacute; a certains autres acteurs
	$destinataires='';
	$message='';
	$tab_acteurs=get_tab_individu_acteurs($row_rs_individu);
	$tab_mail_unique=array();//evite d'avoir deux fois le meme destinataire (meme adresse mail) dans le champ To:
	$tab_destinataires=array();
	$tab_coderole=array();
	$tab_statutvisa=get_statutvisa();//referent=>01, srhu...tous les roles dont sii, adminfin,...
	// libelles longs des roles acteurs
	$tab_roles_liblong=get_roles_liblong();

	$tab_individu_visas_apposes=get_individu_visas($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$tab_statutvisa);
	/* if(in_array($tab_statutvisa['du'],$tab_individu_visas_apposes) || in_array($tab_statutvisa['srh'],$tab_individu_visas_apposes))
	{ $tab_coderole=array('referent','theme','gesttheme','srh','du','admingestfin');
	}
	else  */
	if(in_array($tab_statutvisa['theme'],$tab_individu_visas_apposes))
	{ $tab_coderole=array('referent','theme','gesttheme');
	}
	else if(in_array($tab_statutvisa['referent'],$tab_individu_visas_apposes))
	{ $tab_coderole=array('referent','theme','gesttheme');
	}
	if(in_array($tab_statutvisa['referent'],$tab_individu_visas_apposes))
	{ $tab_coderole[]='srhue';
	}
	$to="";
	$first=true;
	$tab_codeacteur=array();
	foreach($tab_coderole as $coderole)
	{ foreach($tab_acteurs as $coderoleacteur=>$tab_un_acteur)
		{ if($coderoleacteur==$coderole)
			{ foreach($tab_un_acteur as $i=>$tab_infouser)
				{ if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
					{ $tab_mail_unique[strtolower($tab_infouser['email'])]=$tab_infouser['email'];
						$to.=($first?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom'].' <'.$tab_infouser['email'].'>';
						$first=false;
					}
				}
			}
		}
	}
	//le user expediteur s'il n'est pas deja dans $to
	$tab_infouser=get_info_user($codeuser);
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}
	

	switch ($action)
	{	case "invalider" :
			$mot_action="Invalidation";
			$phrase_action="Le dossier n&deg; ".$row_rs_individu['codeindividu']." a &eacute;t&eacute; invalid&eacute;";
			break;
		case "supprimer" :
			$rs=mysql_query("select * from individusejour  where codeindividu=".GetSQLValueString($row_rs_individu['codeindividu'], "text")) or die(mysql_error());
			if(mysql_num_rows($rs)==1)// un seul sejour : suppression de l'individu et du séjour
			{ $mot_action="suppression";
				$phrase_action="Le dossier n&deg; ".$row_rs_individu['codeindividu']." a &eacute;t&eacute; supprim&eacute;";
			}
			else
			{ $mot_action="Suppression du s&eacute;jour";
				$phrase_action="Le s&eacute;jour du dossier n&deg; ".$row_rs_individu['codeindividu']." a &eacute;t&eacute; supprim&eacute;";
			}
			mysql_free_result($rs);
			break;
		default :
			break;
	}
	$subject="Pour information : ".$mot_action." du dossier de ".$row_rs_individu['libciv']." ".$row_rs_individu['prenom']." ".$row_rs_individu['nom'];

	$message="";
	$message.="Bonjour,\n\n";
	$message.=$phrase_action." sur le serveur 12+ par ".$tab_infouser['prenom']." ".$tab_infouser['nom'].".";
	$message.="\n\n (<b>".$mot_action."</b>)";
	$message.="\n".$row_rs_individu['libciv']." ".$row_rs_individu['prenom']." ".$row_rs_individu['nom']." (".$row_rs_individu['libcorps'].")";
	$message.="\nS&eacute;jour du&nbsp;".aaaammjj2jjmmaaaa($row_rs_individu['datedeb_sejour'],"/")."&nbsp;&nbsp;au ".aaaammjj2jjmmaaaa($row_rs_individu['datefin_sejour'],"/");
	$message.="\n".$GLOBALS['libcourt_theme_fr']." :&nbsp;".$row_rs_individu['theme'];
	$message.="\n\n";
	$message.="cordialement,";
	$message.="\n\n";
	$message.="Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";	
	
	if($GLOBALS['mode_exploit']=='test')
	{ $message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}


	$subject=	html_entity_decode($subject);
	
	$from = $GLOBALS['Serveur12+']['nom'].'<'.$GLOBALS['Serveur12+']['email'].'>';
	$replyto= $GLOBALS['webMaster']['nom'].'<'.$GLOBALS['webMaster']['email'].'>';
	
	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto,'Subject' => $subject);
 	//--------------- modifs pour mime
	//$text = $message;
	$message=nl2br($message);
	// TESTE SUR PC ET MAC : OK : $message.=detailindividu($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$codeuser);

	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime("\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);

	//fin mime
 	$erreur=""; 
	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message_html_txt);//envoimail($tab_destinataires, $headers, $message);
	}
	else
	{ $erreur=$message;
	}	
  if(isset($rs_individuaction))mysql_free_result($rs_individuaction);
	
	return $erreur;
}

function mail_validation_individu($row_rs_individu,$codeuser,$codevisa_a_apposer)
{ // $row_rs_individu['demander_autorisation'] est transmis dans gestionindividus : evite transmission des infos pour calculer demander_autorisation
	/* destinataires de message : 
  'referent' : referent, gesttheme, resptheme, srh
	'srhue' : referent, gesttheme, resptheme1,...
	'theme' : referent, gesttheme, resptheme1,..., srh
  */
  // le user codeuser n'est pas destinataire (&eacute;ventuel) du message envoy&eacute; a certains autres acteurs
	$tab_acteurs=get_tab_individu_acteurs($row_rs_individu);
	$tab_destinataires=array();
	$tab_mail_unique=array();//evite d'avoir deux fois le meme destinataire (meme adresse mail) dans le champ To:
	$tab_statutvisa=get_statutvisa();//referent=>01, ...tous les roles dont sii, adminfin,...
	$codevisa_a_apposer_lib=array_search($codevisa_a_apposer,$tab_statutvisa);
	$texte_visa_appose="";
	$tab_statutvisa['gesttheme']='';
	
  foreach($tab_acteurs as $coderoleacteur=>$tab_acteurs_par_role)
  { foreach($tab_acteurs_par_role as $ieme_acteur=>$tab_info_un_acteur_du_role)
		{ $un_destinataire=array('codeacteur'=>$tab_info_un_acteur_du_role['codeindividu'],'prenomnom'=>$tab_info_un_acteur_du_role['prenom'].' '.
																	$tab_info_un_acteur_du_role['nom'],
																'email'=>$tab_info_un_acteur_du_role['email']);
			if($codevisa_a_apposer_lib=='referent')
			{ if($coderoleacteur=='referent' || $coderoleacteur=='gesttheme' || $coderoleacteur=='srhue' || $coderoleacteur=='theme')
				{ $tab_destinataires[]=$un_destinataire;
					$texte_visa_appose="Nouvel arrivant";
				}
			}
			else if($codevisa_a_apposer_lib=='srhue')
			{ if($coderoleacteur=='referent' || $coderoleacteur=='gesttheme'  || $coderoleacteur=='srhue'  || $coderoleacteur=='admingestfin')
				{ $tab_destinataires[]=$un_destinataire;
					$texte_visa_appose="Autorisation d'acc&egrave;s au laboratoire";
				}
			}
			else if($codevisa_a_apposer_lib=='theme')
			{ if($coderoleacteur=='referent' || $coderoleacteur=='gesttheme' || $coderoleacteur=='theme')
				{ $tab_destinataires[]=$un_destinataire;
					$texte_visa_appose="Visa d'arriv&eacute;e";
				}
			}
		}
  }
	
	$tab_infouser=get_info_user($codeuser);
	$subject="Pour information : validation du dossier de ".$row_rs_individu['libciv']." ".$row_rs_individu['prenom']." ".$row_rs_individu['nom'];
	if(isset($row_rs_individu['texte_attente_sujet']) && $row_rs_individu['texte_attente_sujet']!='')
	{ $subject.=" (".$row_rs_individu['texte_attente_sujet'].")";
	}
	$message="";
	$message.="Bonjour,<br><br>";
	$message.="Le dossier n&deg; ".$row_rs_individu['codeindividu']." a &eacute;t&eacute; valid&eacute; sur le serveur 12+ par ".$tab_infouser['prenom']." ".$tab_infouser['nom'].".";
	$message.="<br><br> (<b>".$texte_visa_appose."</b>)";
	$message.="<br>".$row_rs_individu['libciv']." ".$row_rs_individu['prenom']." ".$row_rs_individu['nom']." (".$row_rs_individu['libcorps'].")";
	$message.="<br>S&eacute;jour du&nbsp;".aaaammjj2jjmmaaaa($row_rs_individu['datedeb_sejour'],"/")."&nbsp;&nbsp;au ".aaaammjj2jjmmaaaa($row_rs_individu['datefin_sejour'],"/");
	$message.="<br>".$GLOBALS['libcourt_theme_fr']." :&nbsp;".$row_rs_individu['theme'];
	$message.="<br>T&eacute;l. :&nbsp;".$row_rs_individu['tel']."&nbsp;&nbsp;&nbsp;&nbsp;Mail : ".$row_rs_individu['email'];
	$message.="<br>Lieu de travail : ".($row_rs_individu['liblieu']==''?$row_rs_individu['autrelieu']:$row_rs_individu['liblieu']);
	if(($row_rs_individu['codelibcat']=='STAGIAIRE' &&  $row_rs_individu['sujetstageobligatoire']=='oui')
		 || $row_rs_individu['codelibcat']=='DOCTORANT' 
		 || ($row_rs_individu['codelibcat']=='POSTDOC' && $row_rs_individu['codesujet']!='')
		 || ($row_rs_individu['codelibcat']=='EXTERIEUR' && isset($row_rs_individu['texte_attente_sujet']) && $row_rs_individu['texte_attente_sujet']!=''))
	{ $message.="<br>Sujet : ".$row_rs_individu['titresujet'];
		$message.=(isset($row_rs_individu['texte_attente_sujet']) && $row_rs_individu['texte_attente_sujet']!='')?'&nbsp;(<font color="#FF0000">'.$row_rs_individu['texte_attente_sujet'].'</font>)':'';
	}
	$message.="<br><br>";
	$message.="cordialement,";
	$message.="<br><br>";
	$message.="Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";	
	
	$subject=	html_entity_decode($subject);
	
	$from = $GLOBALS['Serveur12+']['nom'].'<'.$GLOBALS['Serveur12+']['email'].'>';
	$replyto= $GLOBALS['webMaster']['nom'].'<'.$GLOBALS['webMaster']['email'].'>';
	
	$to="";
	$first=true;
	foreach($tab_destinataires as $un_destinataire=>$tab_un_destinataire)
	{ if(!array_key_exists(strtolower($tab_un_destinataire['email']),$tab_mail_unique) && est_mail($tab_un_destinataire['email']))
		{ $tab_mail_unique[strtolower($tab_un_destinataire['email'])]=$tab_un_destinataire['email'];
			$to.=($first?"":", ").$tab_un_destinataire['prenomnom'].' <'.$tab_un_destinataire['email'].'>';
			$first=false;
		}
	}
	//le user expediteur s'il n'est pas deja dans $to
	$tab_infouser=get_info_user($codeuser);
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}

	
	// apposition du visa theme : message accueil
	if($codevisa_a_apposer_lib=='theme')
	{ $query_rs_individuaction= "select * from individuaction".
															" where codeindividu=".GetSQLValueString($row_rs_individu['codeindividu'], "text").
															" and numsejour=".GetSQLValueString($row_rs_individu['numsejour'], "text")." and codelibaction='msgaccueil'";
		$rs_individuaction=mysql_query($query_rs_individuaction);
		if(mysql_num_rows($rs_individuaction)==0)
		{ if($GLOBALS['mode_exploit']=='test')
			{ $to.=", TEST cran-direction <".$GLOBALS['emailTest'].">, TEST ACMO <".$GLOBALS['emailTest'].">, TEST Serv. Info. <".$GLOBALS['emailTest'].">";//test
			}
			else
			{ $to.=", cran-direction <".$GLOBALS['emailDIRECTION'].">, ACMO <".$GLOBALS['emailACMO'].">, SID <".$GLOBALS['emailSID'].">";
			}
		}
	}
	
	if($GLOBALS['mode_exploit']=='test')
	{ $message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}

	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto,'Subject' => $subject);
 //--------------- modifs pour mime
// TESTE SUR PC ET MAC : OK : $message.=detailindividu($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$codeuser);

	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'"styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime("\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);

	//fin mime
	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message_html_txt);//envoimail($tab_destinataires, $headers, $message);
	}
	else
	{ $erreur=$message;
	}
  if(isset($rs_individuaction))mysql_free_result($rs_individuaction);
	
	return $erreur;
}

function mail_validation_declaration_fsd($codeindividu,$numsejour,$codeuser,$_post_val_user)
{ // mail de dde de declaration fsd
	$tab_infouser=get_info_user($codeuser);
	$tab_mail_unique=array();
	$tab_destinataires=array();
	$mime = new Mail_mime("\n");
	
  // roles srh, admingestfin (provenant de) structure
  $rs=mysql_query("select codeindividu as coderesp,codelib from structureindividu,structure".
									" where structureindividu.codestructure=structure.codestructure".
									" and (codelib=".GetSQLValueString('srh', "text")." or codelib=".GetSQLValueString('admingestfin', "text").")".
									" and structureindividu.estresp='oui'") or die(mysql_error());
  $i=0;
	while($row_rs = mysql_fetch_assoc($rs))
  { $i++;
		$tab_destinataires[$row_rs['codelib']][$i]=get_info_user($row_rs['coderesp']);
  }
  // role srhue pour le role srh
  /* if(array_key_exists('srh',$tab_destinataires))
  { list($i,$tab)=each($tab_destinataires['srh']);
		$tab_destinataires['srhue'][1]=$tab_destinataires['srh'][$i];
  } */
  if(isset($rs))mysql_free_result($rs);

	$query_rs_user= "select tel,fax,email,lieu.liblonglieu as liblieu from individu,lieu ".
									" where codeindividu=".GetSQLValueString($codeuser, "text").
									" and individu.codelieu=lieu.codelieu";
	$rs_user=mysql_query($query_rs_user);
	$row_rs_user=mysql_fetch_assoc($rs_user);
	$query_rs_individu=	"select civilite.libcourt_fr as libciv, if(nomjf='',nom,nomjf) as nompatronymique, prenom,numdossierzrr,codegesttheme from individu,individusejour,civilite".
											" where individu.codeciv=civilite.codeciv and individu.codeindividu=".GetSQLValueString($codeindividu,"text").
											" and individu.codeindividu=individusejour.codeindividu and numsejour=".GetSQLValueString($numsejour,"text");
	$rs_individu=mysql_query($query_rs_individu) or die(mysql_error());
	$row_rs_individu=mysql_fetch_assoc($rs_individu);

	$tab_destinataires['codegesttheme'][1]=get_info_user($row_rs_individu['codegesttheme']);
	
	$query_rs_individupj=	"select individupj.*,typepjindividu.* from individupj,typepjindividu".
												" where individupj.codetypepj=typepjindividu.codetypepj".
												" and individupj.codelibcatpj=typepjindividu.codelibcatpj".
												" and individupj.codelibcatpj=".GetSQLValueString('sejour', "text").
												" and (typepjindividu.codelibtypepj=".GetSQLValueString('cv', "text").
												"			 or typepjindividu.codelibtypepj=".GetSQLValueString('fsd', "text").")".
												" and individupj.numcatpj=".GetSQLValueString($numsejour, "text").
												" and codeindividu=".GetSQLValueString($codeindividu, "text") or die(mysql_error());
	$rs_individupj=mysql_query($query_rs_individupj);

	$subject="Protection du Potentiel Scientifique et Technique de la Nation - ".$GLOBALS['acronymelabo']." UMR 7039 (".
						$row_rs_individu['numdossierzrr']." - ".$row_rs_individu['libciv']." ".$row_rs_individu['prenom']." ".$row_rs_individu['nompatronymique'].")";
	$message="";
	$message.="Monsieur ".$GLOBALS['fsd_contact_ul']['prenomnom'].",";
	$message.="<br><br>Je vous prie de bien vouloir trouver ci-joint, le formulaire de demande accompagn&eacute; du CV concernant ";
	$message.='<b>'.$row_rs_individu['libciv']." ".$row_rs_individu['prenom'].' '.strtoupper($row_rs_individu['nompatronymique']).'</b>';
	$message.="<br><br>Restant &agrave; votre disposition pour tout compl&eacute;ment d'information, ";
	$message.="veuillez agr&eacute;er, Monsieur ".$GLOBALS['fsd_contact_ul']['prenomnom'].", mes salutations distingu&eacute;es.";
	$message.="<br><br>".$tab_infouser['prenom'].' '.$tab_infouser['nom'];
	$message.="<br>--";
	$message.="<br>".$GLOBALS['acronymelabo']." - CNRS - UMR 7039";
	$message.="<br>".$row_rs_user['liblieu'];
	$message.="<br>T&eacute;l. : ".$row_rs_user['tel']."&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Fax : ".$row_rs_user['fax'];
	$message.="<br>Mail : ".$row_rs_user['email'];
	
	$subject=	html_entity_decode($subject);
	
	$from = $tab_infouser['prenom'].' '.$tab_infouser['nom'].'<'.$GLOBALS['Serveur12+']['email'].'>';
	$replyto= $tab_infouser['prenom'].' '.$tab_infouser['nom'].'<'.$tab_infouser['email'].'>';
	$to="";
	$to.=$GLOBALS['fsd_contact_ul']['prenomnom'].' <'.$GLOBALS['fsd_contact_ul']['email'].'>';

	$first=true;
	foreach($tab_destinataires as $un_role=>$tab_un_role)
	{ foreach($tab_un_role as $i=>$tab_un_destinataire)
		if(!array_key_exists(strtolower($tab_un_destinataire['email']),$tab_mail_unique) && est_mail($tab_un_destinataire['email']))
		{	$tab_mail_unique[strtolower($tab_un_destinataire['email'])]=$tab_un_destinataire['email'];
			$to.=($to=='')?"":", ".$tab_un_destinataire['prenom'].' '.$tab_un_destinataire['nom'].' <'.$tab_un_destinataire['email'].'>';
			$first=false;
		}
	}
	//le user expediteur s'il n'est pas deja dans $to
	$tab_infouser=get_info_user($codeuser);
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}


	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}
	
	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto,'Subject' => $subject);
 //--------------- modifs pour mime
// TESTE SUR PC ET MAC : OK : $message.=detailindividu($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$codeuser);

	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime->setHTMLBody($html_message);
	while($row_rs_individupj=mysql_fetch_assoc($rs_individupj))
	{ $filename = explode('.', $row_rs_individupj['nomfichier']);
		$filenameext = $filename[count($filename)-1];
		$mime->addAttachment ($GLOBALS['path_to_rep_upload'] .'/individu/'.$codeindividu.'/sejour/'.$numsejour.'/'.$row_rs_individupj['codetypepj'], $GLOBALS['file_types_mime_array'][$filenameext] , $row_rs_individupj['nomfichier']);
	}
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);
	//fin mime

	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message_html_txt);
	}
	else
	{ $erreur=$subject.'<br><br>'.$message;
	}
	//$erreur=$message_html_txt;

  if(isset($rs_user))mysql_free_result($rs_user);

	return $erreur;
}

/* ---------------------------------------- CONTRATS --------------------------------------------------- 
																VISAS ET ROLES par user + workflow 																		 
*/
// liste des visas possible et des roles : il n'y a pas de statutvisa
function get_contrat_statutvisa()
{ return array();
}

function get_tab_contrat_roleuser($codeuser,$codecontrat,$tab_contrat_statutvisa,$estreferent,$estresptheme)
{ $tab_result=array();
	$tab_roleuser=array();// table des roles
	// roles du, sif, admingestfin, gestcnrs et gestul(provenant de) structure
 	$rs_structureindividu=mysql_query("select codeindividu,codelib from structureindividu,structure".
																		" where structureindividu.codestructure=structure.codestructure".
																		" and (codelib=".GetSQLValueString('sif', "text")." or codelib=".GetSQLValueString('du', "text").
																		" 			or codelib=".GetSQLValueString('gestcnrs', "text").
																		"       or codelib=".GetSQLValueString('admingestfin', "text").
																		"       or codelib=".GetSQLValueString('gestul', "text").")") or die(mysql_error()); //and estresp='oui'
  while($row_rs_structureindividu = mysql_fetch_assoc($rs_structureindividu))
  { if($row_rs_structureindividu['codeindividu']==$codeuser)
    { if($row_rs_structureindividu['codelib']=='sif')
			{ $tab_roleuser[$row_rs_structureindividu['codelib'].'#1']=$tab_cmd_statutvisa[$row_rs_structureindividu['codelib'].'#1'];
    		$tab_roleuser[$row_rs_structureindividu['codelib'].'#2']=$tab_cmd_statutvisa[$row_rs_structureindividu['codelib'].'#2'];
			}
			else
			{ $tab_roleuser[$row_rs_structureindividu['codelib']]=$tab_cmd_statutvisa[$row_rs_structureindividu['codelib']];
			}
		}
  }
	
	$tab_result['tab_roleuser']=$tab_roleuser;
  $tab_result['estreferent']=$estreferent;
  $tab_result['estresptheme']=$estresptheme;

  if(isset($rs_commande)) mysql_free_result($rs_commande);
  if(isset($rs_respthemecommande)) mysql_free_result($rs_respthemecommande);
  if(isset($rs_structureindividu)) mysql_free_result($rs_structureindividu);
  if(isset($rs_secrsite)) mysql_free_result($rs_secrsite);
  if(isset($rs)) mysql_free_result($rs);
	
  return $tab_result;



}
/* ---------------------------------------- COMMANDES --------------------------------------------------- 
																VISAS ET ROLES par user + workflow 																		 
*/
// liste des visas possible et des roles
function get_cmd_statutvisa()
{ $tab_cmd_statutvisa=array();
  $rs_cmd_statutvisa=mysql_query("select codestatutvisa,coderole from cmd_statutvisa where codestatutvisa<>'' order by codestatutvisa") or die(mysql_error());
  while($row_rs_cmd_statutvisa = mysql_fetch_assoc($rs_cmd_statutvisa))
  { $tab_cmd_statutvisa[$row_rs_cmd_statutvisa['coderole']]=$row_rs_cmd_statutvisa['codestatutvisa']; 
  }
  mysql_free_result($rs_cmd_statutvisa);  
  return $tab_cmd_statutvisa;
}

function get_cmd_statutvisa_texte_visa_title()
{ $tab_cmd_statutvisa_texte_visa_title=array();
  $rs_cmd_statutvisa_texte_visa_title=mysql_query("select coderole,texte_cmd_statutvisa_title from cmd_statutvisa where codestatutvisa<>'' order by codestatutvisa") or die(mysql_error());
  while($row_rs_cmd_statutvisa_texte_visa_title = mysql_fetch_assoc($rs_cmd_statutvisa_texte_visa_title))
  { $tab_cmd_statutvisa_texte_visa_title[$row_rs_cmd_statutvisa_texte_visa_title['coderole']]=$row_rs_cmd_statutvisa_texte_visa_title['texte_cmd_statutvisa_title']; 
  }
  mysql_free_result($rs_cmd_statutvisa_texte_visa_title);  
  return $tab_cmd_statutvisa_texte_visa_title;
}
//liste des statutvisa deja apposes pour cette commande 
function get_cmd_visas($codecommande,$tab_cmd_statutvisa)
{ //------------------ VISAS (roles) : $codecommande a deja un ou plusieurs visas $tab_individustatutvisa apposes dans la liste de tous les visas (roles) $tab_statutvisa
	// referent=>01, srhue=>02,...
  $tab_commandestatutvisa=array();
  $query_rs_commandestatutvisa="SELECT commandestatutvisa.*,coderole from commandestatutvisa,cmd_statutvisa".
															 " where commandestatutvisa.codestatutvisa=cmd_statutvisa.codestatutvisa and commandestatutvisa.codecommande=".GetSQLValueString($codecommande, "text").
															 " order by commandestatutvisa.codestatutvisa";
  $rs_commandestatutvisa=mysql_query($query_rs_commandestatutvisa) or die(mysql_error()); 
  while($row_rs_commandestatutvisa = mysql_fetch_assoc($rs_commandestatutvisa))
  { $tab_commandestatutvisa[$row_rs_commandestatutvisa['coderole']]=$tab_cmd_statutvisa[$row_rs_commandestatutvisa['coderole']];
  }
  
  mysql_free_result($rs_commandestatutvisa);
  return $tab_commandestatutvisa;

}

// roles user pour une commande ou son ensemble
function get_tab_cmd_roleuser($codeuser,$codecommande,$tab_cmd_statutvisa,$estreferent,$estresptheme,$estrespcontrat)
{ // renvoie table $tab_result['tab_roleuser']=$tab_roleuser
	//               $tab_result['estreferent']=$estreferent
	//               $tab_result['estresptheme']=$estreferent;
	// $tab_roleuser contient la liste des roles d'un individu : referent, theme, contrat, du pour le directeur, secrsite, sif, admingestfin, gestcnrs et gestul 
	$tab_result=array();
	$tab_roleuser=array();// table des roles
  // roles referent
  if($codecommande!='')
	{ $rs_commande=mysql_query("select codereferent,codesecrsite,codecreateur,codemodifieur".
		  				 							" from commande where codecommande=".GetSQLValueString($codecommande, "text")) or die(mysql_error());
		$row_rs_commande = mysql_fetch_assoc($rs_commande);
		if($codeuser==$row_rs_commande['codereferent'] || $codeuser==$row_rs_commande['codesecrsite'] || $codeuser==$row_rs_commande['codecreateur'] || $codeuser==$row_rs_commande['codemodifieur'])
		{ $tab_roleuser['referent']=$tab_cmd_statutvisa['referent'];//le role referent est donne a la personne qui valide cette saisie
		}
		$estreferent=($codeuser==$row_rs_commande['codereferent']);
		//secrsite pour commande !=''
		if($codeuser==$row_rs_commande['codesecrsite'])
		{ $tab_roleuser['secrsite']=$tab_cmd_statutvisa['secrsite'];
		}
	}
	else
	{ // role secrsite en general 
		$query_rs_secrsite="select * from secrsite where secrsite.codesecrsite=".GetSQLValueString($codeuser, "text");
		$rs_secrsite=mysql_query($query_rs_secrsite) or die(mysql_error());
		$nb_rs_secrsite = mysql_num_rows($rs_secrsite);		
		if($nb_rs_secrsite>0)
		{ $tab_roleuser['secrsite']=$tab_cmd_statutvisa['secrsite'];
		}
	}
	// role theme si resp. en tant que resptheme de façon generale si $codecommande='', sinon pour $codecommande
	$query_rs="select * from  commandeimputationbudget,centrecouttheme,structureindividu".
						" where commandeimputationbudget.codecentrecout=centrecouttheme.codecentrecout and commandeimputationbudget.codeeotp=''".
						" and centrecouttheme.codestructure=structureindividu.codestructure ".
						($codecommande==""?"":" and commandeimputationbudget.codecommande = ".GetSQLValueString($codecommande, "text")).
						" and structureindividu.codeindividu = ".GetSQLValueString($codeuser, "text").
						" and commandeimputationbudget.virtuel_ou_reel='0'";
  $rs=mysql_query($query_rs);
  if(mysql_num_rows($rs)!=0)
  { $tab_roleuser['theme']=$tab_cmd_statutvisa['theme'];
    $estresptheme=true;
  }
	// role contrat si resp contrat
	$query_rs="select commandeimputationbudget.codecontrat from  commandeimputationbudget,contrat,individu".
						" where commandeimputationbudget.codecontrat=contrat.codecontrat".
						" and commandeimputationbudget.codecontrat<>''".
						($codecommande==""?"":" and commandeimputationbudget.codecommande = ".GetSQLValueString($codecommande, "text")).
						" and individu.codeindividu = contrat.coderespscientifique".
						" and individu.codeindividu <>''".
						" and commandeimputationbudget.virtuel_ou_reel='0'".
						" union".
						" select commandeimputationbudget.codecontrat from  commandeimputationbudget,budg_aci,individu".
						" where commandeimputationbudget.codecontrat=budg_aci.codeaci".
						" and commandeimputationbudget.codecontrat<>''".
						($codecommande==""?"":" and commandeimputationbudget.codecommande = ".GetSQLValueString($codecommande, "text")).
						" and individu.codeindividu = budg_aci.coderespaci".
						" and individu.codeindividu <>''".
						" and commandeimputationbudget.virtuel_ou_reel='0'";
	$rs=mysql_query($query_rs);
  if(mysql_num_rows($rs)!=0)//c'est un contrat
	{ $query_rs="select commandeimputationbudget.codecontrat from  commandeimputationbudget,contrat,individu".
							" where commandeimputationbudget.codecontrat=contrat.codecontrat".
							" and commandeimputationbudget.codecontrat<>''".
							($codecommande==""?"":" and commandeimputationbudget.codecommande = ".GetSQLValueString($codecommande, "text")).
							" and individu.codeindividu = contrat.coderespscientifique".
							" and individu.codeindividu = ".GetSQLValueString($codeuser, "text").
							" and commandeimputationbudget.virtuel_ou_reel='0'".
							" union".
							" select commandeimputationbudget.codecontrat from  commandeimputationbudget,budg_aci,individu".
							" where commandeimputationbudget.codecontrat=budg_aci.codeaci".
							" and commandeimputationbudget.codecontrat<>''".
							($codecommande==""?"":" and commandeimputationbudget.codecommande = ".GetSQLValueString($codecommande, "text")).
							" and individu.codeindividu = budg_aci.coderespaci".
							" and individu.codeindividu = ".GetSQLValueString($codeuser, "text").
							" and commandeimputationbudget.virtuel_ou_reel='0'";

		$rs=mysql_query($query_rs);
		if(mysql_num_rows($rs)==0)// le user n'est pas resp de ce contrat
		{ $estrespcontrat=false;
		}
		else
		{ $tab_roleuser['contrat']=$tab_cmd_statutvisa['contrat'];
			$estrespcontrat=true;
		}
	}

  // roles du, sif, admingestfin, gestcnrs et gestul(provenant de) structure
 	$rs_structureindividu=mysql_query("select codeindividu,codelib from structureindividu,structure".
																		" where structureindividu.codestructure=structure.codestructure".
																		" and (codelib=".GetSQLValueString('sif', "text")." or codelib=".GetSQLValueString('du', "text").
																		" 			or codelib=".GetSQLValueString('gestcnrs', "text").
																		"       or codelib=".GetSQLValueString('admingestfin', "text").
																		"       or codelib=".GetSQLValueString('gestul', "text").")") or die(mysql_error()); //and estresp='oui'
  while($row_rs_structureindividu = mysql_fetch_assoc($rs_structureindividu))
  { if($row_rs_structureindividu['codeindividu']==$codeuser)
    { if($row_rs_structureindividu['codelib']=='sif')
			{ $tab_roleuser[$row_rs_structureindividu['codelib'].'#1']=$tab_cmd_statutvisa[$row_rs_structureindividu['codelib'].'#1'];
    		$tab_roleuser[$row_rs_structureindividu['codelib'].'#2']=$tab_cmd_statutvisa[$row_rs_structureindividu['codelib'].'#2'];
			}
			else
			{ $tab_roleuser[$row_rs_structureindividu['codelib']]=$tab_cmd_statutvisa[$row_rs_structureindividu['codelib']];
			}
		}
  }
	$tab_result['tab_roleuser']=$tab_roleuser;
  $tab_result['estreferent']=$estreferent;
  $tab_result['estresptheme']=$estresptheme;
  $tab_result['estrespcontrat']=$estrespcontrat;

  if(isset($rs_commande)) mysql_free_result($rs_commande);
  if(isset($rs_respthemecommande)) mysql_free_result($rs_respthemecommande);
  if(isset($rs_structureindividu)) mysql_free_result($rs_structureindividu);
  if(isset($rs_secrsite)) mysql_free_result($rs_secrsite);
  if(isset($rs)) mysql_free_result($rs);
	
  return $tab_result;

}

function get_tab_cmd_acteurs($row_rs_commande)
{ $codecommande=$row_rs_commande['codecommande'];
	$liste_acteurs=array();
  $tab_acteurs['referent'][1]=get_info_user($row_rs_commande['codereferent']);
	$tab_acteurs['secrsite'][1]=get_info_user($row_rs_commande['codesecrsite']);
	$query_rs="(select distinct budg_contrat_source_vue.coderespscientifique as coderespcontrat,'contrat' as typeresp from  commandeimputationbudget,budg_contrat_source_vue".
						" where commandeimputationbudget.codecontrat=budg_contrat_source_vue.codecontrat".
						" and commandeimputationbudget.codecontrat<>''".
						" and budg_contrat_source_vue.coderespscientifique <>''".
						" and commandeimputationbudget.virtuel_ou_reel='0' and commandeimputationbudget.codecommande=".GetSQLValueString($row_rs_commande['codecommande'], "text").")".
						" UNION".
						" (select distinct structureindividu.codeindividu as coderespcontrat,'theme' as typeresp".
						" from  commandeimputationbudget,budg_contrat_source_vue,centrecouttheme,structureindividu".
						" where budg_contrat_source_vue.coderespscientifique=''".
						" and commandeimputationbudget.codecontrat<>''".
						" and commandeimputationbudget.virtuel_ou_reel='0' and commandeimputationbudget.codecommande=".GetSQLValueString($row_rs_commande['codecommande'], "text").
						" and commandeimputationbudget.codecontrat=budg_contrat_source_vue.codecontrat".
						" and budg_contrat_source_vue.codecentrecout=centrecouttheme.codecentrecout".
						" and centrecouttheme.codestructure=structureindividu.codestructure".")";
  $rs=mysql_query($query_rs);
	$i=0;
	while($row_rs = mysql_fetch_assoc($rs))
  { $i++;
		$tab_acteurs[$row_rs['typeresp']][$i]=get_info_user($row_rs['coderespcontrat']);
  }

 // par defaut de respcontrat ET de resptheme : le directeur
	if(!isset($tab_acteurs['contrat'][1]) && !isset($tab_acteurs['theme'][1]))
	{ $query_rs="select codeindividu as coderesp,codelib from structureindividu,structure".
								    " where structureindividu.codestructure=structure.codestructure".
								    " and codelib=".GetSQLValueString('du', "text")." and structureindividu.estresp='oui'";
		$rs=mysql_query($query_rs) or die(mysql_error());
		$row_rs = mysql_fetch_assoc($rs);
		$tab_acteurs['theme'][1]=get_info_user($row_rs['coderesp']);
	}
// roles du, sif (provenant de) structure
  $rs=mysql_query("select codeindividu as coderesp,codelib from structureindividu,structure".
								    " where structureindividu.codestructure=structure.codestructure".
								    " and (codelib=".GetSQLValueString('sif', "text").
										" or codelib=".GetSQLValueString('du', "text").") and structureindividu.estresp='oui'") or die(mysql_error());
	$i=0;
  while($row_rs = mysql_fetch_assoc($rs))
	{ $i++;
		$tab_acteurs[$row_rs['codelib']][$i]=get_info_user($row_rs['coderesp']);
  }
	if(isset($rs))mysql_free_result($rs);
  return $tab_acteurs;
}

function get_cmd_roles_liblong()
{ // libelles 'longs' des roles acteurs
	$tab_roles_liblong=array();
	$rs=mysql_query("select coderole, liblong from cmd_statutvisa where codestatutvisa<>'' order by codestatutvisa") or die(mysql_error());
  while($row_rs = mysql_fetch_assoc($rs))
  { $tab_roles_liblong[$row_rs['coderole']]=$row_rs['liblong']; 
  }
	if(isset($rs))mysql_free_result($rs);
  return $tab_roles_liblong;

}


function contenu_cmd_col_role_droit($tab_commandestatutvisa,$tab_roleuser,$estrespcontrat,$colstatutvisa,$a_valider_par_resp)
{ /*
	$tab_individustatutvisa = liste des visas deja apposes
	$tab_roleuser=liste des roles du user codeuser
	$colstatutvisa=colonne concernee 
  */
  $contenu="";//ne doit pas etre vide pour les colonnes de roles a afficher : mettre n/a s'il n'y a rien a mettre d'autre
  $droit="read";// valeur par defaut de droit (read/write) du role $role 
  if($colstatutvisa=='referent') 
  { // si visa 'referent' appose pour $codecommande
		if(array_key_exists('referent',$tab_commandestatutvisa))
		{ $contenu = "visa appose";
		} 
		else // le visa 'referent' n'est pas appose pour $codecommande
		{ if(array_key_exists('referent',$tab_roleuser) || $_SESSION['b_cmd_etre_admin'])// $codeuser a le role 'referent' meme si le referent r&eacute;el n'est pas lui
	  	{ $droit="write";	  
	    	$contenu = "valider";
	  	}
      else// $codeuser n'a pas le role 'referent'
	  	{ $contenu = "brancher";
	  	}
		}	
  }
  else if($colstatutvisa=='theme' || $colstatutvisa=='contrat')// visa 'theme' ou contrat
  {	if(array_key_exists('theme',$tab_commandestatutvisa) || array_key_exists('contrat',$tab_commandestatutvisa)) // visa 'theme'  ou contrat appose
		{ $contenu = "visa appose";
		} 
		else // visa 'theme'  ou contrat n'est pas appose
		{ if((array_key_exists('theme',$tab_roleuser) && $estrespcontrat) || (array_key_exists('contrat',$tab_roleuser) && $estrespcontrat) || $_SESSION['b_cmd_etre_admin'])
			{ if(!array_key_exists('referent',$tab_commandestatutvisa))//visa referent non appose
		  	{ $contenu = "sablier";
		  	}
		  	else //visa referent appose
		  	{ if($a_valider_par_resp  || $_SESSION['b_cmd_etre_admin'])
					{ $droit="write";
		    		$contenu = "valider";
					}
					else
					{ $contenu = "brancher";
					}
		  	}
	    }
      else // $codeuser n'a pas le role 'theme' ou contrat
	    { if(!array_key_exists('referent',$tab_commandestatutvisa))//visa referent non appose 
		  	{ $contenu = "sablier";
		  	}
        else
        { $contenu ="brancher";
		  	}
			}
	  }
  }
  else if($colstatutvisa=='sif#1')// visa 'sif#1'
  { // visa 'sif' deja appose ?
		if(array_key_exists('sif#1',$tab_commandestatutvisa))// visa 'sif' deja appose
		{ $contenu = "visa appose";
		} 
		else // visa 'sif' non appose
		{ if(!array_key_exists('theme',$tab_commandestatutvisa) && !array_key_exists('contrat',$tab_commandestatutvisa))//visa theme ou contrat non appose
			{ $contenu = "sablier";
			}
			else//visa theme ou contrat appose
			{ if(array_key_exists('sif#1',$tab_roleuser))// visa 'referent' et 'theme' appose et role sif
		  	{ $droit="write";
		 	  	$contenu = "valider";
		 		}
      	else// $codeuser n'a pas le role 'sif'
		 		{ $contenu = "brancher";
	   		}
    	}
  	}
  }
  else if($colstatutvisa=='secrsite')// visa 'secrsite'
  { // visa 'secrsite' deja appose ?
		if(array_key_exists('secrsite',$tab_commandestatutvisa))// visa 'secrsite' deja appose
		{ $contenu = "visa appose";
		} 
		else // visa 'secrsite' non appose
		{ if(!array_key_exists('sif#1',$tab_commandestatutvisa))//visa sif#1 non appose
			{ $contenu = "sablier";
			}
			else//visa 'secrsite' appose
			{ if(array_key_exists('secrsite',$tab_roleuser) || $_SESSION['b_cmd_etre_admin'])// visa 'referent' et 'theme' appose et role secrsite
		  	{ $droit="write";
		 	  	$contenu = "valider";
		 		}
      	else// $codeuser n'a pas le role 'sif'
		 		{ $contenu = "brancher";
	   		}
    	}
  	}
  }
  else if($colstatutvisa=='sif#2')// visa 'sif#2'
  { // visa 'sif#2' deja appose ?
		if(array_key_exists('sif#2',$tab_commandestatutvisa))// visa 'sif#2' deja appose
		{ $contenu = "visa appose";
		} 
		else // visa 'sif' non appose
		{ if(!array_key_exists('secrsite',$tab_commandestatutvisa))//visa theme non appose
			{ $contenu = "sablier";
			}
			else//visa theme appose
			{ if(array_key_exists('sif#2',$tab_roleuser))// visa 'referent' et 'theme' appose et role sif
		  	{ $droit="write";
		 	  	$contenu = "valider";
		 		}
      	else// $codeuser n'a pas le role 'sif'
		 		{ $contenu = "brancher";
	   		}
    	}
  	}
  }
  $tab_contenu_col_role_droit[$colstatutvisa]['droit']=$droit;
  $tab_contenu_col_role_droit[$colstatutvisa]['colonne']=$contenu;
  return $tab_contenu_col_role_droit;
}

function popup_validation_contrat($codecontrat,$codeuser)
{ $destinataires='';
	$message='';
	$tab_acteurs=array();
	$tab_destinataires=array();
	// roles du, sif, admingestfin (provenant de) structure
  $rs=mysql_query("select codeindividu as coderesp,codelib from structureindividu,structure".
									" where structureindividu.codestructure=structure.codestructure".
									" and (codelib=".GetSQLValueString('sif', "text")." or codelib=".GetSQLValueString('admingestfin', "text").
									/* " or codelib=".GetSQLValueString('du', "text"). */") and structureindividu.estresp='oui'") or die(mysql_error());
	$i=0;
  while($row_rs = mysql_fetch_assoc($rs))
	{ $i++;
		$tab_acteurs[$row_rs['codelib']][$i]=get_info_user($row_rs['coderesp']);
  }
  foreach($tab_acteurs as $coderoleacteur=>$tab_acteurs_par_role)
  { foreach($tab_acteurs_par_role as $ieme_acteur=>$tab_info_un_acteur_du_role)
		{ $un_destinataire=array('codeacteur'=>$tab_info_un_acteur_du_role['codeindividu'],'prenomnom'=>$tab_info_un_acteur_du_role['prenom'].' '.
																	$tab_info_un_acteur_du_role['nom'],
																'coderoleacteur'=>$coderoleacteur);
			$tab_destinataires[]=$un_destinataire;
		}
	}
	// libelles longs des roles acteurs
	$tab_roles_liblong=get_cmd_roles_liblong();

	//suppression des doublons de noms de destinataires et une ligne par destinataire avec son ou ses roles en libelle long
	$tab_destinataire_roles=array();
	foreach($tab_destinataires as $un_destinataire)
	{ if(array_key_exists($un_destinataire['codeacteur'],$tab_destinataire_roles))
		{ $tab_destinataire_roles[$un_destinataire['codeacteur']].=', '.$tab_roles_liblong[$un_destinataire['coderoleacteur'].($un_destinataire['coderoleacteur']=='sif'?"#1":"")];
		}
		else
		{ $tab_destinataire_roles[$un_destinataire['codeacteur']]='- '.$un_destinataire['prenomnom'].' : '.$tab_roles_liblong[$un_destinataire['coderoleacteur'].($un_destinataire['coderoleacteur']=='sif'?"#1":"")];
		}
	}
	
  $message.=addslashes("Cette action informe les destinataires que le contrat ".$codecontrat." fait partie de la base contrats.")."\\n";
	$message.="Un mail va &ecirc;tre envoy&eacute; &agrave; :"."\\n";
	foreach($tab_destinataire_roles as $codeacteur=>$ligne_destinataire)
	{ $message.=addslashes($ligne_destinataire)."\\n";
	}

	if(isset($rs))mysql_free_result($rs);
	return $message;
}

function mail_validation_contrat($codecontrat,$codeuser)
{ $destinataires='';
	$message='';
	$tab_acteurs=array();
	$tab_destinataires=array();
	$tab_mail_unique=array();
	// roles du, sif, admingestfin (provenant de) structure
  $query_rs="select codeindividu as coderesp,codelib from structureindividu,structure".
						" where structureindividu.codestructure=structure.codestructure".
						" and (codelib=".GetSQLValueString('sif', "text")." or codelib=".GetSQLValueString('admingestfin', "text").
						/* " or codelib=".GetSQLValueString('du', "text"). */") and structureindividu.estresp='oui'";
	$rs=mysql_query($query_rs) or die(mysql_error());
	$i=0;
  while($row_rs = mysql_fetch_assoc($rs))
	{ $i++;
		$tab_acteurs[$row_rs['codelib']][$i]=get_info_user($row_rs['coderesp']);
  }
	$to="";
	$first=true;
  foreach($tab_acteurs as $coderoleacteur=>$tab_acteurs_par_role)
  { foreach($tab_acteurs_par_role as $ieme_acteur=>$tab_info_un_acteur_du_role)//ecrasement de l'index dans $tab_destinataires pour mail unique
		{ if(!array_key_exists(strtolower($tab_info_un_acteur_du_role['email']),$tab_mail_unique) && est_mail($tab_info_un_acteur_du_role['email']))
			{ $tab_mail_unique[strtolower($tab_info_un_acteur_du_role['email'])]=$tab_info_un_acteur_du_role['email'];
				$to.=($first?"":", ").$tab_info_un_acteur_du_role['prenom'].' '.$tab_info_un_acteur_du_role['nom'].' <'.$tab_info_un_acteur_du_role['email'].'>';
				$first=false;
			}
		}
	}
	//le user expediteur s'il n'est pas deja dans $to
	$tab_infouser=get_info_user($codeuser);
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}

	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}
	
	$rs_contrat=mysql_query("select contrat.*, individu.nom, individu.prenom,libcourtorggest as liborggest from contrat, individu, cont_orggest ".
													" where contrat.coderespscientifique=individu.codeindividu ".
													" and contrat.codeorggest=cont_orggest.codeorggest".
													" and codecontrat=".GetSQLValueString($codecontrat, "text")) or die(mysql_error());
	$row_rs_contrat = mysql_fetch_assoc($rs_contrat);
	
	$tab_infouser=get_info_user($codeuser);
	$subject="Pour information : validation du contrat ".$codecontrat." (".substr($row_rs_contrat['ref_contrat'],0,30).")";
	$message="";
	$message.="Le contrat n&deg; ".$codecontrat." a &eacute;t&eacute; valid&eacute; sur le serveur 12+ par ".$tab_infouser['prenom']." ".$tab_infouser['nom'].".";
	$message.="<br><br><b>R&eacute;f&eacute;rence du contrat : </b>".$row_rs_contrat['ref_contrat'];
	$message.="<br><b>Du </b>".aaaammjj2jjmmaaaa($row_rs_contrat['datedeb_contrat'],'/')."&nbsp;<b>au</b> ".aaaammjj2jjmmaaaa($row_rs_contrat['datefin_contrat'],'/');
	$message.="<br><b>Organisme gestionnaire des cr&eacute;dits : </b>".$row_rs_contrat['liborggest'];
	$message.="<br><b>Responsable scientifique : </b>".$row_rs_contrat['prenom'].' '.$row_rs_contrat['nom'];
	$message.="<br><b>Montant : </b>".$row_rs_contrat['montant_ht']." &euro;";
	$message.="<br><br><b>Sujet</b> : ".$row_rs_contrat['sujet'];
	$message.="<br><br>";
	$message.="<br><br>Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";	
	
	$subject=	html_entity_decode($subject);
	
 	$from = $GLOBALS['Serveur12+']['nom'].'<'.$GLOBALS['Serveur12+']['email'].'>';
	$replyto= $GLOBALS['Serveur12+']['nom'].'<'.$GLOBALS['Serveur12+']['email'].'>';

	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto,'Subject' => $subject);
 //--------------- modifs pour mime
// TESTE SUR PC ET MAC : OK : $message.=detailindividu($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$codeuser);

	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime("\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);
	//fin mime

 	$erreur="";
	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message_html_txt);
	}
	else
	{ $erreur=$subject.'<br><br>'.$message;
	}

	if(isset($rs_contrat))mysql_free_result($rs_contrat);
	if(isset($rs))mysql_free_result($rs);
	return $erreur;
}

function mail_validation_commande($row_rs_commande,$codeuser,$codevisa_a_apposer,$envoyer_mail_srh)
{ /* destinataires de message : 
  'referent' : referent, secrsite, resptheme ou respcontrat
	'theme' ou 'contrat' : referent, secrsite, resptheme1,...,sif
	'sif#1' : secrsite, sif (et srh si salaire)
	'secrsite' : sif, maif
	'sif#2' : referent, gesttheme, resptheme1,..., srh
  */
  // le user codeuser n'est pas destinataire (&eacute;ventuel) du message envoy&eacute; a certains autres acteurs
	$numaction='';//permet d'indiquer le numero d'action #1, #2 de sif
	$tab_destinataires=array();
	$tab_mail_unique=array();//evite d'avoir deux fois le meme destinataire (meme adresse mail) dans le champ To:
	$tab_statutvisa=get_cmd_statutvisa();//referent=>01, ...tous les roles dont sii, adminfin,...
	$codevisa_a_apposer_lib=array_search($codevisa_a_apposer,$tab_statutvisa);
	$texte_visa_appose="";
	$codecommande=$row_rs_commande['codecommande'];
	$tab_commandeimputationbudget=array();
	$tab_acteurs=get_tab_cmd_acteurs($row_rs_commande);
	$texte_info_imputation="";
	$demandeur='';
	$nomp_missionnaire='';
	$texte_info_mission='';
	$message="";
	$subject="";
	$tab_contrat_a_viser=array();	
	$tab_commandeimputationbudget_du_codeuser_de_la_commande=array();
	$tab_commandeimputationbudget_statutvisa_de_la_commande=array();
	//salaires
	if(($row_rs_commande['codenature']=='06' || $row_rs_commande['codenature']=='12') && $codevisa_a_apposer_lib=='sif#1' && $envoyer_mail_srh)//codenature salaire 06 et 12
	{ $rs=mysql_query("select codeindividu as coderesp,codelib from structureindividu,structure".
										" where structureindividu.codestructure=structure.codestructure".
										" and (codelib=".GetSQLValueString('srh', "text").
										" or codelib=".GetSQLValueString('admingestfin', "text").
										" or codelib=".GetSQLValueString('gestperscontrat', "text").") and structureindividu.estresp='oui'") or die(mysql_error());


		$i=0;
		while($row_rs = mysql_fetch_assoc($rs))
		{ $i++;
			$tab_acteurs[$row_rs['codelib']][$i]=get_info_user($row_rs['coderesp']);
		}
		
	}
	
	$query="select nom as referentnom, prenom as referentprenom from individu ".
				 " where individu.codeindividu=".GetSQLValueString($row_rs_commande['codereferent'], "text");
	$rs=mysql_query($query) or die(mysql_error());
	if($row_rs=mysql_fetch_assoc($rs))
	{ $demandeur=$row_rs['referentprenom'].' '.$row_rs['referentnom'];
	}
	// modif 01/2014 ajout code mission sur visa sif#1
	if($row_rs_commande['codemission']!='')
	{ $texte_info_mission.='<b>Mission '.($codevisa_a_apposer_lib=='sif#1'?'('.$row_rs_commande['codemission'].')':'').'</b> : ';
		$query_rs_mission="select codeagent,nom, prenom, motif from mission where codemission=".GetSQLValueString($row_rs_commande['codemission'], "text");
		$rs_mission=mysql_query($query_rs_mission);
		if($row_rs_mission=mysql_fetch_assoc($rs_mission))
		{ $nomp_missionnaire=$row_rs_mission['nom']." ".substr($row_rs_mission['prenom'],0,1);
			$texte_info_mission.=$row_rs_mission['motif'];
			if($row_rs_mission['codeagent']=='')
			{ $texte_info_mission.="(".$row_rs_mission['nom']." ".$row_rs_mission['prenom'].")";
			}
		}
	}
	// 20/01/2014 plus d'une imput. virt.
	$viser_la_commande_totalement=true;
	if(($codevisa_a_apposer_lib=='theme' || $codevisa_a_apposer_lib=='contrat') && !$_SESSION['b_cmd_etre_admin'])
	{	//imputations de la commande
		$query_rs="select numordre,codecontrat from commandeimputationbudget where codecommande=".GetSQLValueString($codecommande, "text")." and virtuel_ou_reel='0'";
		$rs=mysql_query($query_rs);
		if(mysql_num_rows($rs)>1)// plus d'une imputation	virtuelle	
		{	//$viser_la_commande_totalement=false;
			while($row_rs=mysql_fetch_assoc($rs))
			{ $tab_commandeimputationbudget_de_la_commande[$row_rs['codecontrat']]=$row_rs['numordre'];
			}
			// imputations dont le codeuser est resp.
			$tab_commandeimputationbudget_du_codeuser_de_la_commande=array();
			$query_rs="select distinct commandeimputationbudget.codecontrat from  commandeimputationbudget,budg_contrat_source_vue,individu".
								" where commandeimputationbudget.codecontrat=budg_contrat_source_vue.codecontrat".
								" and commandeimputationbudget.codecontrat<>''".
								" and (			(individu.codeindividu = budg_contrat_source_vue.coderespscientifique and individu.codeindividu = ".GetSQLValueString($codeuser, "text").")".
								"				or  (budg_contrat_source_vue.coderespscientifique='' ".
														" and budg_contrat_source_vue.codecentrecout in (select codecentrecout from centrecouttheme,structureindividu".
																																						" where centrecouttheme.codestructure=structureindividu.codestructure".
																																						" and structureindividu.codeindividu = ".GetSQLValueString($codeuser, "text").")".
														")".
								"			)".
								" and commandeimputationbudget.virtuel_ou_reel='0' and commandeimputationbudget.codecommande=".GetSQLValueString($codecommande, "text");
			$rs=mysql_query($query_rs);
			while($row_rs=mysql_fetch_assoc($rs))
			{ $tab_commandeimputationbudget_du_codeuser_de_la_commande[$row_rs['codecontrat']]=$row_rs['codecontrat'];
			}
			$query_rs="select codecontrat,codestatutvisa".
								" from commandeimputationbudget_statutvisa".
								" where codecommande=".GetSQLValueString($codecommande, "text")."and (codestatutvisa='02' or codestatutvisa='03')";
			$rs=mysql_query($query_rs);
			while($row_rs=mysql_fetch_assoc($rs))
			{ $tab_commandeimputationbudget_statutvisa_de_la_commande[$row_rs['codecontrat']]=$row_rs['codestatutvisa'];
			}
			foreach($tab_commandeimputationbudget_de_la_commande as $uncodecontrat=>$numordre)
			{ if(array_key_exists($uncodecontrat,$tab_commandeimputationbudget_du_codeuser_de_la_commande) && !array_key_exists($uncodecontrat,$tab_commandeimputationbudget_statutvisa_de_la_commande))
				{	$tab_contrat_a_viser[$uncodecontrat]=$numordre;
				}
			}
			// toutes les imputations visas=on enleve celles deja visees et on verifie que celles de $tab_contrat_a_viser sont les dernieres 
			$query_rs="select codecontrat". 
								" from commandeimputationbudget".
								" where codecommande=".GetSQLValueString($codecommande, "text")." and virtuel_ou_reel='0'".
								" and codecontrat not in (select codecontrat from commandeimputationbudget_statutvisa where codecommande=".GetSQLValueString($codecommande, "text").
																					" and (codestatutvisa='02' or codestatutvisa='03')".")";
			$rs=mysql_query($query_rs);
			while($row_rs=mysql_fetch_assoc($rs))//toutes les imputations ont le visa 'theme' ou 'contrat'
			{ $viser_la_commande_totalement=$viser_la_commande_totalement && array_key_exists($row_rs['codecontrat'],$tab_contrat_a_viser);
			}
		}
	}
	// fin 20/01/2014 plus d'une imput. virt.
	$query_rs="(SELECT commandeimputationbudget.codecommande, commandeimputationbudget.codecontrat as codecontrat,commandeimputationbudget.codeeotp as codeeotp,".
						" typecredit.codetypecredit,typecredit.libcourt as libtypecredit, centrefinancier.libcourt as libcentrefinancier,".
						" centrecout.libcourt as libcentrecout,'' as libcentrecout_reel,'' as libcentrefinancier_reel,cmd_typesource.codetypesource,cmd_typesource.libcourt as libtypesource,".
						" budg_contrat_source_vue.coderespscientifique,respscientifique.prenom,respscientifique.nom,acronyme as libcontrat,'' as libeotp,contrat_ou_source,'' as eotp_ou_source,".
						" virtuel_ou_reel,montantengage,montantpaye,commandeimputationbudget.numordre".
						" from commandeimputationbudget, typecredit,centrefinancier,centrecout,budg_contrat_source_vue,cmd_typesource,individu as respscientifique".
						" where commandeimputationbudget.codetypecredit=typecredit.codetypecredit".
						" and commandeimputationbudget.codecentrefinancier=centrefinancier.codecentrefinancier".
						" and commandeimputationbudget.codecentrecout=centrecout.codecentrecout".
						" and commandeimputationbudget.virtuel_ou_reel='0' and commandeimputationbudget.codecontrat=budg_contrat_source_vue.codecontrat and budg_contrat_source_vue.coderespscientifique=respscientifique.codeindividu and budg_contrat_source_vue.codetypesource=cmd_typesource.codetypesource".
						" and commandeimputationbudget.codecommande=".GetSQLValueString($codecommande, "text").
						" order by virtuel_ou_reel,commandeimputationbudget.numordre".')'.
						" UNION".
						" (SELECT commandeimputationbudget.codecommande, commandeimputationbudget.codecontrat as codecontrat,commandeimputationbudget.codeeotp as codeeotp,".
						" typecredit.codetypecredit,typecredit.libcourt as libtypecredit, centrefinancier.libcourt as libcentrefinancier,".
						" centrecout.libcourt as libcentrecout,centrecout_reel.libcourt as libcentrecout_reel,centrefinancier_reel.libcourt as libcentrefinancier_reel,cmd_typesource.codetypesource,cmd_typesource.libcourt as libtypesource,".
						" budg_eotp_source_vue.coderespscientifique,respscientifique.prenom,respscientifique.nom,'' as libcontrat,libeotp,'' as contrat_ou_source,eotp_ou_source,".
						" virtuel_ou_reel,montantengage,montantpaye,commandeimputationbudget.numordre".
						" from commandeimputationbudget, typecredit,centrefinancier,centrecout,centrecout_reel,centrefinancier_reel,budg_eotp_source_vue,cmd_typesource,individu as respscientifique".
						" where commandeimputationbudget.codetypecredit=typecredit.codetypecredit".
						" and commandeimputationbudget.codecentrefinancier=centrefinancier.codecentrefinancier".
						" and commandeimputationbudget.codecentrecout=centrecout.codecentrecout".
						" and commandeimputationbudget.virtuel_ou_reel='1' and commandeimputationbudget.codeeotp=budg_eotp_source_vue.codeeotp and budg_eotp_source_vue.coderespscientifique=respscientifique.codeindividu and budg_eotp_source_vue.codetypesource=cmd_typesource.codetypesource".
						" and budg_eotp_source_vue.codecentrecout_reel=centrecout_reel.codecentrecout_reel".
						" and centrecout_reel.codecentrefinancier_reel=centrefinancier_reel.codecentrefinancier_reel".
						" and commandeimputationbudget.codecommande=".GetSQLValueString($codecommande, "text").
						" order by virtuel_ou_reel,commandeimputationbudget.numordre".')';
	$rs=mysql_query($query_rs) or die(mysql_error());
	while($row_rs=mysql_fetch_assoc($rs))
	{ if($row_rs['virtuel_ou_reel']=='0') //demande
		{ if($row_rs['contrat_ou_source']=='contrat')
			{ $row_rs['libcontrat']=$row_rs['nom'].' '.substr($row_rs['prenom'],0,1).'. - '.$row_rs['libcontrat'];
			}
			else // source
			{ /* $rs1=mysql_query( "select libcourt as libcentrecout_reel from budg_eotp_source_vue,centrecout_reel, budg_contrateotp_source_vue".
													" where budg_eotp_source_vue.codecentrecout_reel=centrecout_reel.codecentrecout_reel".
													" and budg_contrateotp_source_vue.codecontrat=".GetSQLValueString($row_rs['codecontrat'], "text").
													" and budg_contrateotp_source_vue.codeeotp=budg_eotp_source_vue.codeeotp") or die(mysql_error());
				$libcentrecout_reel='';
				if($row_rs1=mysql_fetch_assoc($rs1))
				{ $libcentrecout_reel=$row_rs1['libcentrecout_reel'];
				} */
				$tab_construitsource=array(	'codetypesource'=>$row_rs['codetypesource'],'libtypesource'=>$row_rs['libtypesource'],
																		'libsource'=>$row_rs['libcontrat'],'libcentrecout_reel'=>'',//$libcentrecout_reel
																		'coderespscientifique'=>$row_rs['coderespscientifique'],'nomrespscientifique'=>$row_rs['nom'],
																		'prenomrespscientifique'=>$row_rs['prenom'],'codetypecredit'=>$row_rs['codetypecredit']);//'CNRS-UL'
				$row_rs['libcontrat']=construitlibsource($tab_construitsource);
				$row_rs['libtypecredit']='CNRS-UL';
			}
		}
		else // reel
		{ if($row_rs['eotp_ou_source']=='eotp')
			{ $row_rs['libeotp']=$row_rs['nom'].' '.substr($row_rs['prenom'],0,1).'. - '.$row_rs['libeotp'];
			}
			else
			{ $tab_construitsource=array(	'codetypesource'=>$row_rs['codetypesource'],'libtypesource'=>$row_rs['libtypesource'],
																		'libsource'=>$row_rs['libeotp'],'libcentrecout_reel'=>$row_rs['libcentrecout_reel'],
																		'coderespscientifique'=>$row_rs['coderespscientifique'],'nomrespscientifique'=>$row_rs['nom'],
																		'prenomrespscientifique'=>$row_rs['prenom'],'codetypecredit'=>$row_rs['codetypecredit']);
				$row_rs['libeotp']=construitlibsource($tab_construitsource);
			}
		}
		$tab_commandeimputationbudget[$row_rs['virtuel_ou_reel']][$row_rs['numordre']]=$row_rs;
	}
	if($codevisa_a_apposer_lib=='referent' || $codevisa_a_apposer_lib=='theme' || $codevisa_a_apposer_lib=='contrat')
	{ $virtuel_ou_reel='0';
	}
	else
	{ $virtuel_ou_reel='1';
	}
	/* if(isset($tab_commandeimputationbudget[$virtuel_ou_reel]['01']['libtypecredit']))
	{ $tab_commandeimputationbudget_virtuel_ou_reel=$tab_commandeimputationbudget[$virtuel_ou_reel];
		$texte_info_imputation.='<b>Imputation &nbsp;&nbsp;&nbsp;Cr&eacute;dits : </b>'.$tab_commandeimputationbudget[$virtuel_ou_reel]['01']['libtypecredit'];
		$first=true;
		foreach($tab_commandeimputationbudget_virtuel_ou_reel as $numordre=>$une_commandeimputationbudget)
		{ if(!$first)
			{ $texte_info_imputation.='<br>';
			}
			$first=false;
			$color="#000000";
			if($virtuel_ou_reel=='0')
			{ if(array_key_exists($une_commandeimputationbudget['codecontrat'],$tab_commandeimputationbudget_du_codeuser_de_la_commande))
				{ $color="#993399"; 
				}
				else if(array_key_exists($une_commandeimputationbudget['codecontrat'],$tab_commandeimputationbudget_statutvisa_de_la_commande))
				{ $color="#00CC00";
				}
			}
			$texte_info_imputation.='<font color="'.$color.'">';
			$texte_info_imputation.='<b>&nbsp;&nbsp;&nbsp;Enveloppe : </b>'.$une_commandeimputationbudget['libcentrecout'];
			if($virtuel_ou_reel=='0')// contrat si virtuel
			{ $texte_info_imputation.='<b>&nbsp;&nbsp;&nbsp;Source/contrat : </b>'.$une_commandeimputationbudget['libcontrat'];
			}
			if($virtuel_ou_reel=='1')// eotp si reel
			{ $texte_info_imputation.='<b>&nbsp;&nbsp;&nbsp;Source/EOTP : </b>'.$une_commandeimputationbudget['libeotp'];
			}
			$texte_info_imputation.='<b>&nbsp;&nbsp;&nbsp;Montant : </b>'.$une_commandeimputationbudget['montantengage'];
			if($codevisa_a_apposer_lib=='sif#1' || $codevisa_a_apposer_lib=='secrsite' || $codevisa_a_apposer_lib=='sif#2')
			{ $texte_info_imputation.="&nbsp;&nbsp;&nbsp;<br><b>Centre financier : </b>".$une_commandeimputationbudget['libcentrefinancier_reel']."&nbsp;&nbsp;&nbsp;<b>Centre de co&ucirc;t : </b>".$une_commandeimputationbudget['libcentrecout_reel'];
			}
			$texte_info_imputation.='</font>';
		}
	} */
 	if(isset($tab_commandeimputationbudget[$virtuel_ou_reel]['01']['libtypecredit']))
	{ $tab_commandeimputationbudget_virtuel_ou_reel=$tab_commandeimputationbudget[$virtuel_ou_reel];
		$texte_info_imputation.='<table>';
		 
		$first=true;
		foreach($tab_commandeimputationbudget_virtuel_ou_reel as $numordre=>$une_commandeimputationbudget)
		{ $texte_info_imputation.='<tr><td nowrap>';
			if($first)
			{ $texte_info_imputation.='<b>Imputation(s)</b>';
				$first=false;
			}
			$texte_info_imputation.='</td>';
			$color="#000000";
			if($virtuel_ou_reel=='0')
			{ if(array_key_exists($une_commandeimputationbudget['codecontrat'],$tab_commandeimputationbudget_du_codeuser_de_la_commande))
				{ $color="#993399"; 
				}
				else if(array_key_exists($une_commandeimputationbudget['codecontrat'],$tab_commandeimputationbudget_statutvisa_de_la_commande))
				{ $color="#00CC00";
				}
			}
			$texte_info_imputation.='<td nowrap><font color="'.$color.'"><b>Cr&eacute;dits : </b></td><td nowrap>'.$une_commandeimputationbudget['libtypecredit'].'</font></td>';
			$texte_info_imputation.='<font color="'.$color.'">';
			$texte_info_imputation.='<td nowrap><font color="'.$color.'"><b>Enveloppe : </b></td><td nowrap>'.$une_commandeimputationbudget['libcentrecout'].'</font></td>';
			$texte_info_imputation.='';
			if($virtuel_ou_reel=='0')// contrat si virtuel
			{ $texte_info_imputation.='<td nowrap><font color="'.$color.'"><b>Source/contrat : </b></td><td nowrap>'.$une_commandeimputationbudget['libcontrat'].'</font></td>';
			}
			if($virtuel_ou_reel=='1')// eotp si reel
			{ $texte_info_imputation.='<td nowrap><font color="'.$color.'"><b>&nbsp;&nbsp;&nbsp;Source/EOTP : </b></td><td nowrap>'.$une_commandeimputationbudget['libeotp'].'</font></td><td>';
			}
			$texte_info_imputation.='';
			$texte_info_imputation.='<td nowrap><font color="'.$color.'"><b>&nbsp;&nbsp;&nbsp;Montant : </b></td><td nowrap>'.$une_commandeimputationbudget['montantengage'].'</font></td>';
			$texte_info_imputation.='</tr>';
		}
		$texte_info_imputation.='</table>';
		// sorti du for, le pointeur est sur la dernniere imputation reelle qui contient, comme les autres,  libcentrefinancier et reel
		if($codevisa_a_apposer_lib=='sif#1' || $codevisa_a_apposer_lib=='secrsite' || $codevisa_a_apposer_lib=='sif#2')
		{ $texte_info_imputation.="&nbsp;&nbsp;&nbsp;<br><b>Centre financier : </b>".$une_commandeimputationbudget['libcentrefinancier_reel']."&nbsp;&nbsp;&nbsp;<b>Centre de co&ucirc;t : </b>".$une_commandeimputationbudget['libcentrecout_reel'];
		}
	}

  foreach($tab_acteurs as $coderoleacteur=>$tab_acteurs_par_role)
  { foreach($tab_acteurs_par_role as $ieme_acteur=>$tab_info_un_acteur_du_role)
		{ $un_destinataire=array('codeacteur'=>$tab_info_un_acteur_du_role['codeindividu'],'prenomnom'=>$tab_info_un_acteur_du_role['prenom'].' '.
																	$tab_info_un_acteur_du_role['nom'],
																'email'=>$tab_info_un_acteur_du_role['email']);
			if($codevisa_a_apposer_lib=='referent')
			{	if(/* $coderoleacteur=='referent'  ||*/ $coderoleacteur=='theme' || $coderoleacteur=='contrat' || $coderoleacteur=='sif'  || $coderoleacteur=='secrsite' )
				{ $tab_destinataires[]=$un_destinataire;
					if($coderoleacteur=='sif');
					{ $numaction='#1';
					}
					$texte_visa_appose="Nouvelle commande";
				}
			}
			else if($codevisa_a_apposer_lib=='theme')
			{ if(/* $coderoleacteur=='referent' || $coderoleacteur=='secrsite' || $coderoleacteur=='theme' ||  */$coderoleacteur=='sif')
				{ $tab_destinataires[]=$un_destinataire;
					$texte_visa_appose='Visa'.($viser_la_commande_totalement?'':'&nbsp;partiel').'&nbsp;Resp. cr&eacute;dits';
					//$texte_visa_appose='Visa'.($viser_la_commande_totalement?'':'&nbsp;partiel').'&nbsp;'.$GLOBALS['libcourt_theme_fr'];
					if($coderoleacteur=='sif');
					{ $numaction='#1';
					}
				}
			}
			else if($codevisa_a_apposer_lib=='contrat')
			{ if(/* $coderoleacteur=='referent' || $coderoleacteur=='secrsite' || $coderoleacteur=='contrat' ||  */$coderoleacteur=='sif')
				{ $tab_destinataires[]=$un_destinataire;
					$texte_visa_appose='Visa'.($viser_la_commande_totalement?'':'&nbsp;partiel').'&nbsp;Resp. cr&eacute;dits';
					if($coderoleacteur=='sif');
					{ $numaction='#1';
					}
				}
			}
			else if($codevisa_a_apposer_lib=='sif#1')
			{ if($coderoleacteur=='sif' || $coderoleacteur=='secrsite' || $coderoleacteur=='srh'  || $coderoleacteur=='admingestfin'
				 || $coderoleacteur=='gestperscontrat')
				{ $tab_destinataires[]=$un_destinataire;
					if($coderoleacteur=='sif');
					{ $numaction='#1';
					}
					$texte_visa_appose="Visa Ing&eacute;nierie d'ex&eacute;cution budg&eacute;taire (centre de co&ucirc;t et EOTP)";
				}
			}
			else if($codevisa_a_apposer_lib=='secrsite')
			{ if($coderoleacteur=='sif'/*  || $coderoleacteur=='secrsite' */)
				{ $tab_destinataires[]=$un_destinataire;
					$numaction='#2';
				}
				$texte_visa_appose='Visa MIGO';
			}
			else if($codevisa_a_apposer_lib=='sif#2')
			{ if($coderoleacteur=='sif')
				{ $tab_destinataires[]=$un_destinataire;
					$numaction='#2';
				}
				$texte_visa_appose="Visa Ing&eacute;nierie d'ex&eacute;cution budg&eacute;taire (Paiement)";
			}
		}
  }

	$tab_infouser=get_info_user($codeuser);
	if($codevisa_a_apposer_lib=='referent')
	{ $subject.="URGENT - POUR VALIDATION -";
	}
	else
	{ $subject.="Pour information : validation de la";
	}
	$subject.=" commande ".$codecommande." (".$row_rs_commande['objet'].")".($row_rs_commande['codemission']!=''?" - Mission de : ".$nomp_missionnaire:'');
	$message.="Bonjour,<br><br>";
	$message.="La commande n&deg; ".$codecommande." a &eacute;t&eacute; valid&eacute;e sur le serveur 12+ par ".$tab_infouser['prenom']." ".$tab_infouser['nom'].".";
	$message.="<br><br> (<b>".$texte_visa_appose."</b>)".($row_rs_commande['estavoir']=='oui'?' <b>Avoir de commande</b>':'');
	$message.="<br><br><b>Demandeur : </b>".$demandeur;
	$message.="<br>".$texte_info_mission;
	$message.="<br><b>Objet : </b>".$row_rs_commande['objet'];
	if(($row_rs_commande['codenature']=='06' || $row_rs_commande['codenature']=='12') && $codevisa_a_apposer_lib=='sif#1')//codenature salaire 06 et 12
	{ $message.="<br><b>D&eacute;tail : </b>".nl2br($row_rs_commande['description']);
	}
	$message.="<br><b>Fournisseur : </b>".$row_rs_commande['libfournisseur'];
	$message.="<br>".$texte_info_imputation;
	$message.=($codevisa_a_apposer_lib=='referent'?'<br><br>Le responsable de contrat/source de cr&eacute;dits est invit&eacute; &agrave; valider la commande sur le'.
																								'&nbsp;<a href="'.$GLOBALS['Serveur12+commande']['lien'].'">'.$GLOBALS['Serveur12+commande']['nom'].'</a>'.
																								'<br><br>Pour toute question relative &agrave; cette commande, veuillez adresser un mail &agrave; <a href="mailto:'.
																								$GLOBALS['Serveur12+commande']['emailretour'].'?subject=Commande%20'.$codecommande.'">Carole Courrier</a>'
																								:"");
	$message.="<br><br>cordialement,";
	$message.="<br><br>Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";	
	
	
	$subject=	html_entity_decode($subject);
	
 	$from = $GLOBALS['Serveur12+commande']['nom'].'<'.$GLOBALS['Serveur12+commande']['emailexpediteur'].'>';
	$replyto= $GLOBALS['Serveur12+commande']['nom'].'<'.$GLOBALS['Serveur12+commande']['emailretour'].'>';
 /*	$from = $GLOBALS['expediteur_commande']['nom'].'<'.$$GLOBALS['expediteur_commande']['email'].'>';
	$replyto= $GLOBALS['expediteur_commande']['nom'].'<'.$GLOBALS['expediteur_commande']['email'].'>';
	*/
	$to="";
	$first=true;
	foreach($tab_destinataires as $un_destinataire=>$tab_un_destinataire)
	{ if(!array_key_exists(strtolower($tab_un_destinataire['email']),$tab_mail_unique) && est_mail($tab_un_destinataire['email']))
		{ $tab_mail_unique[strtolower($tab_un_destinataire['email'])]=$tab_un_destinataire['email'];
			$to.=($first?"":", ").$tab_un_destinataire['prenomnom'].' <'.$tab_un_destinataire['email'].'>';
			$first=false;
		}
	}
	//le user expediteur s'il n'est pas deja dans $to
	$tab_infouser=get_info_user($codeuser);
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}
	
	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}

	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto,'Subject' => $subject);
 //--------------- modifs pour mime
// TESTE SUR PC ET MAC : OK : $message.=detailindividu($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$codeuser);

	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime("\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);

	//fin mime
 	$erreur="";
	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message_html_txt);//envoimail($tab_destinataires, $headers, $message);
	}
	else
	{ $erreur=$subject.'<br><br>'.$message;
	}
	if(isset($rs_mission))mysql_free_result($rs_mission);
	if(isset($rs1))mysql_free_result($rs1);
	if(isset($rs))mysql_free_result($rs);
	return $erreur;
}


function mail_validation_mission_assurance($row_rs_mission,$codeuser,$_post_val_user)
{ /* destinataires de message : 
  'secrsite'
  */
	$tab_infouser=get_info_user($codeuser);
	$tab_destinataires=array();
	$tab_mail_unique=array();//evite d'avoir deux fois le meme destinataire (meme adresse mail) dans le champ To:
	$tab_destinataires[]=$GLOBALS['assurancemission_contact_ul_1'];

	$query_rs_user= "select tel,fax,email,lieu.liblonglieu as liblieu from individu,lieu ".
									" where codeindividu=".GetSQLValueString($codeuser, "text").
									" and individu.codelieu=lieu.codelieu";
	$rs_user=mysql_query($query_rs_user);
	$row_rs_user=mysql_fetch_assoc($rs_user);
	
	$subject="Demande d'attestation d'assurance (".$row_rs_mission['prenom']." ".$row_rs_mission['nom'].")";
	$message="";
	$message.="Madame, Monsieur,";
	$message.="<br><br>par le pr&eacute;sent mail, je souhaite vous informer du d&eacute;placement de :";
	$message.="<br>Pr&eacute;nom - Nom : ".$row_rs_mission['prenom'].' '.$row_rs_mission['nom'];
	$message.="<br>Mail : ".$row_rs_mission['email'];
	$message.="<br>Ville - Pays : ".$_post_val_user['arriveelieu'];
	$message.="<br>D&eacute;placement effectu&eacute; : ".$_post_val_user['deplacement'];
	$message.="<br>Date de d&eacute;part : ".$_post_val_user['departdate'];
	$message.="<br>Date de retour : ".$_post_val_user['arriveedate'];
	$message.="<br><br>Je vous remercie de bien vouloir m&rsquo;adresser l&rsquo;attestation d&rsquo;assurance par retour de messagerie.";
	$message.="<br><br>Cordialement,";
	$message.="<br><br>".$tab_infouser['prenom'].' '.$tab_infouser['nom'];
	$message.="<br>--";
	$message.="<br>".$GLOBALS['acronymelabo']." – CNRS - UMR 7039";
	$message.="<br>".$row_rs_user['liblieu'];
	$message.="<br>T&eacute;l. : ".$row_rs_user['tel']."&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Fax : ".$row_rs_user['fax'];
	$message.="<br>Mail : ".$row_rs_user['email'];
	
	$subject=	html_entity_decode($subject);
	
	$from = $tab_infouser['prenom'].' '.$tab_infouser['nom'].'<'.$GLOBALS['Serveur12+']['email'].'>';
	$replyto= $tab_infouser['prenom'].' '.$tab_infouser['nom'].'<'.$tab_infouser['email'].'>';

	$to="";
	$first=true;
	foreach($tab_destinataires as $un_destinataire=>$tab_un_destinataire)
	{ if(!array_key_exists(strtolower($tab_un_destinataire['email']),$tab_mail_unique) && est_mail($tab_un_destinataire['email']))
		{ $tab_mail_unique[strtolower($tab_un_destinataire['email'])]=$tab_un_destinataire['email'];
			$to.=($first?"":", ").$tab_un_destinataire['prenomnom'].' <'.$tab_un_destinataire['email'].'>';
			$first=false;
		}
	}	
	//le user expediteur s'il n'est pas deja dans $to
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}
	
	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}
	
	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto,'Subject' => $subject);
 //--------------- modifs pour mime
// TESTE SUR PC ET MAC : OK : $message.=detailindividu($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$codeuser);

	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime("\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);

	//fin mime
 	$erreur=""; 
	if($GLOBALS['mode_avec_envoi_mail'])
	{	$erreur=envoimail($headers, $message_html_txt);
	}
	else
	{ $erreur=$subject.'<br><br>'.$message;
	}

  if(isset($rs_user))mysql_free_result($rs_user);

	return $erreur;
}

function mail_validation_commande_avoir($row_rs_commande,$codeuser)
{ /* destinataires de message : 
  'secrsite'
  */
	$codecommande=$row_rs_commande['codecommande'];
	$tab_infouser=get_info_user($codeuser);
	$tab_destinataires=array();
	$tab_mail_unique=array();//evite d'avoir deux fois le meme destinataire (meme adresse mail) dans le champ To:
	$tab_acteurs=array();
	$demandeur='';
	$query="select nom as referentnom, prenom as referentprenom from individu ".
				 " where individu.codeindividu=".GetSQLValueString($row_rs_commande['codereferent'], "text");
	$rs=mysql_query($query) or die(mysql_error());
	if($row_rs=mysql_fetch_assoc($rs))
	{ $demandeur=$row_rs['referentprenom'].' '.$row_rs['referentnom'];
	}
	$query_rs="SELECT commandeimputationbudget.codecontrat as codecontrat, commandeimputationbudget.codeeotp as codeeotp,".
						" typecredit.libcourt as libtypecredit, centrefinancier.libcourt as libcentrefinancier,".
						" centrecout.libcourt as libcentrecout,acronyme as libcontrat,libeotp,".
						" virtuel_ou_reel,montantengage,montantpaye,commandeimputationbudget.numordre as numordre".
						" from commandeimputationbudget, typecredit,centrefinancier,centrecout,budg_eotp_source_vue,budg_contrat_source_vue left join individu as respscientifique ".
						" on budg_contrat_source_vue.coderespscientifique=respscientifique.codeindividu".
						" where commandeimputationbudget.codetypecredit=typecredit.codetypecredit".
						" and commandeimputationbudget.codecentrefinancier=centrefinancier.codecentrefinancier".
						" and commandeimputationbudget.codecentrecout=centrecout.codecentrecout".
						" and commandeimputationbudget.codecontrat=budg_contrat_source_vue.codecontrat".
						" and commandeimputationbudget.codeeotp=budg_eotp_source_vue.codeeotp".
						" and commandeimputationbudget.codecommande=".GetSQLValueString($codecommande, "text");
	$rs=mysql_query($query_rs) or die(mysql_error());
	$montantengage=0;
	while($row_rs=mysql_fetch_assoc($rs))
	{ $montantengage+=$row_rs['virtuel_ou_reel']=='0'?$row_rs['montantengage']:0;
	}
	// roles du, sif, admingestfin (provenant de) structure
  $query_rs="select codeindividu as coderesp,codelib from structureindividu,structure".
						" where structureindividu.codestructure=structure.codestructure".
						" and codelib=".GetSQLValueString('sif', "text")." and structureindividu.estresp='oui'";
	$rs=mysql_query($query_rs);
	$i=0;
  while($row_rs = mysql_fetch_assoc($rs))
	{ $i++;
		$tab_acteurs[$row_rs['codelib']][$i]=get_info_user($row_rs['coderesp']);
  }
  foreach($tab_acteurs as $coderoleacteur=>$tab_acteurs_par_role)
  { foreach($tab_acteurs_par_role as $ieme_acteur=>$tab_info_un_acteur_du_role)//ecrasement de l'index dans $tab_destinataires pour mail unique
		{ $tab_destinataires[$tab_info_un_acteur_du_role['email']]=array('codeacteur'=>$tab_info_un_acteur_du_role['codeindividu'],'prenomnom'=>$tab_info_un_acteur_du_role['prenom'].' '.$tab_info_un_acteur_du_role['nom'],'email'=>$tab_info_un_acteur_du_role['email']);
		}
	}
	
	$subject="Pour information : Avoir de la commande ".$codecommande;
	$message="";
	$message.="Bonjour,<br><br>";
	if($row_rs_commande['estavoir']=='oui')
	{ $message.="L&rsquo;avoir de la commande n&deg; ".$codecommande." a &eacute;t&eacute; r&eacute;tabli en commande par ".$tab_infouser['prenom']." ".$tab_infouser['nom'];
	}
	else
	{ $message.="Le montant de la commande n&deg; ".$codecommande." a &eacute;t&eacute; transform&eacute; en avoir par ".$tab_infouser['prenom']." ".$tab_infouser['nom'];
	}
	$message.="<br><br><b>Demandeur : </b>".$demandeur;
	$message.="<br><b>Objet : </b>".$row_rs_commande['objet'];
	$message.="<br><b>Fournisseur : </b>".$row_rs_commande['libfournisseur'];
	$message.="<br><b>Montant engag&eacute; : </b>".number_format($montantengage,2,'.',' ');
	$message.="<br><br>Cordialement,";
	$message.="<br><br>Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";	
	
	$subject=	html_entity_decode($subject);
	
	$from = $tab_infouser['prenom'].' '.$tab_infouser['nom'].'<'.$GLOBALS['Serveur12+']['email'].'>';
	$replyto= $tab_infouser['prenom'].' '.$tab_infouser['nom'].'<'.$tab_infouser['email'].'>';
	
	$to="";
	$first=true;
	foreach($tab_destinataires as $un_destinataire=>$tab_un_destinataire)
	{ if(!array_key_exists(strtolower($tab_un_destinataire['email']),$tab_mail_unique) && est_mail($tab_un_destinataire['email']))
		{ $tab_mail_unique[strtolower($tab_un_destinataire['email'])]=$tab_un_destinataire['email'];
			$to.=($first?"":", ").$tab_un_destinataire['prenomnom'].' <'.$tab_un_destinataire['email'].'>';
			$first=false;
		}
	}	
	//le user expediteur s'il n'est pas deja dans $to
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}
	
	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}
	
	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto,'Subject' => $subject);
 //--------------- modifs pour mime
	// TESTE SUR PC ET MAC : OK : $message.=detailindividu($row_rs_individu['codeindividu'],$row_rs_individu['numsejour'],$codeuser);

	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime("\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);

	//fin mime
	if($GLOBALS['mode_avec_envoi_mail'])
	{	$erreur=envoimail($headers, $message_html_txt);
	}
	else
	{ $erreur=$subject.'<br><br>'.$message;
	}
	//$erreur=$message;

	if(isset($rs1))mysql_free_result($rs1);
	if(isset($rs))mysql_free_result($rs);
	return $erreur;
}

/* ------------------------------------ SUJETS : popup et mail ---------------------------------------------
*/
function popup_validation_sujet($typevalidation,$codesujet,$tab_infouser)
{ // $typevalidation=demandevalidation ou validation
	$tab_destinataires=array();
	$message="";
	//expediteur
	$tab_destinataires[$tab_infouser['codeindividu']]=$tab_infouser['prenom']." ".$tab_infouser['nom'];
	// createur
	$rs=mysql_query("select individu.codeindividu,nom,prenom from sujet,individu".
									" where sujet.codesujet=".GetSQLValueString($codesujet, "text").
									" and sujet.codecreateur=individu.codeindividu") or die(mysql_error());
	if($row_rs=mysql_fetch_array($rs))
	{ $tab_destinataires[$row_rs['codeindividu']]=$row_rs['prenom']." ".$row_rs['nom'];
	}
  // dir du sujet 
	$rs=mysql_query(" select individu.codeindividu,nom,prenom from sujetdir,individu".
									" where sujetdir.codesujet=".GetSQLValueString($codesujet,"text").
									" and sujetdir.codedir=individu.codeindividu".
									" order by numordre") or die(mysql_error());
	while($row_rs=mysql_fetch_assoc($rs))
	{ $tab_destinataires[$row_rs['codeindividu']]=$row_rs['prenom']." ".$row_rs['nom'];
	}
	// resp themes concerne
	$query_rs="select individu.codeindividu, nom, prenom from sujettheme,structureindividu,individu".
						" where sujettheme.codetheme=structureindividu.codestructure and structureindividu.codeindividu=individu.codeindividu and estresp='oui'".
						" and sujettheme.codesujet=".GetSQLValueString($codesujet, "text");
	$rs=mysql_query($query_rs) or die(mysql_error());
	while($row_rs=mysql_fetch_assoc($rs))
	{ $tab_destinataires[$row_rs['codeindividu']]=$row_rs['prenom']." ".$row_rs['nom'];
	}

	$message = addslashes("Apr&egrave;s avoir valid&eacute; cette proposition, vous ne pourrez plus la modifier.");
	if($typevalidation=='demandevalidation')
	{ $message .= addslashes(" Seul le Responsable de ".$GLOBALS['libcourt_theme_fr']." y aura acc&egrave;s.");
	}
	$message.= "\\n";
	$message.= addslashes("Un message de validation va &ecirc;tre adress&eacute; &agrave; :");
	foreach($tab_destinataires as $codeindividu=>$undestinataire)
	{ $message.= "\\n"."- ".addslashes($undestinataire);
	}
  if(isset($rs_acteur_du_role_a_prevenir))mysql_free_result($rs_acteur_du_role_a_prevenir);
  if(isset($rs_etudiant))mysql_free_result($rs_etudiant);
  if(isset($rs))mysql_free_result($rs);
	return $message;
}

// mail envoye aux acteurs concernes du sujet 
function mail_validation_sujet($codesujet,$tab_infouser,$coderole_a_prevenir)
{ $sujetaffecte=false;
	$message='';
	$tab_destinataires=array();// destinataires : pas de doublon car ecrasement par $tab_destinataires[$....['codeindividu']]
	$tab_mail_unique=array();//evite d'avoir deux fois le meme destinataire (meme adresse mail) dans le champ To:
	$tab_theme=array();
	$rs_sujet=mysql_query("select sujet.*,individu.codeindividu,nom,prenom,email,".
												" typesujet.libcourt_fr as libtypesujet,libstatutsujet,codelibtypestage,libcourttypestage as libtypestage".
												" from sujet,individu,typesujet,statutsujet,typestage".
												" where sujet.codesujet=".GetSQLValueString($codesujet, "text").
												" and sujet.codecreateur=individu.codeindividu and sujet.codetypesujet=typesujet.codetypesujet".
												" and sujet.codestatutsujet=statutsujet.codestatutsujet and sujet.codetypestage=typestage.codetypestage") or die(mysql_error());
	$row_rs_sujet=mysql_fetch_assoc($rs_sujet);
	//createur
	$tab_destinataires[$row_rs_sujet['codeindividu']]=array('prenomnom'=>$row_rs_sujet['prenom'].' '.$row_rs_sujet['nom'],'email'=>$row_rs_sujet['email']);
	
	$rs_dir=mysql_query("select individu.codeindividu,nom,prenom,email from sujetdir,individu ".
											" where sujetdir.codesujet=".GetSQLValueString($codesujet, "text").
											" and sujetdir.codedir=individu.codeindividu ".
											" order by numordre") or die(mysql_error());
	while($row_rs_dir=mysql_fetch_array($rs_dir))
	{ $tab_destinataires[$row_rs_dir['codeindividu']]=array('prenomnom'=>$row_rs_dir['prenom'].' '.$row_rs_dir['nom'],'email'=>$row_rs_dir['email']);
	}

	$rs_theme=mysql_query("select individu.codeindividu,libcourt_fr as libtheme,nom,prenom,email from sujettheme,structure,structureindividu,individu ".
												" where codesujet=".GetSQLValueString($codesujet, "text").
												" and sujettheme.codetheme=structure.codestructure and structureindividu.estresp='oui'".
												" and structure.codestructure=structureindividu.codestructure and structureindividu.codeindividu=individu.codeindividu".
												" order by structure.codestructure") or die(mysql_error());
	while($row_rs_theme=mysql_fetch_assoc($rs_theme))
	{ $tab_destinataires[$row_rs_theme['codeindividu']]=array('prenomnom'=>$row_rs_theme['prenom'].' '.$row_rs_theme['nom'],'email'=>$row_rs_theme['email']);
		$tab_theme[$row_rs_theme['libtheme']]=$row_rs_theme['libtheme'];//ecrase les doublons eventuels
	}
												
	// message eventuel a la gestionnaire de GT ou au SRH
	if($coderole_a_prevenir!='')
	{ $sujetaffecte=true;
		$rs_etudiant=mysql_query(	"select individu.codeindividu,nom,prenom,codegesttheme from individu,individusejour,individusujet ".
															" where individu.codeindividu=individusejour.codeindividu".
															" and individusejour.codeindividu=individusujet.codeindividu and individusejour.numsejour=individusujet.numsejour".
															" and individusujet.codesujet=".GetSQLValueString($codesujet, "text")) or die(mysql_error());
		$row_rs_etudiant=mysql_fetch_assoc($rs_etudiant);
		/* if($coderole_a_prevenir=='theme')
		{  */
		$rs_acteur_du_role_a_prevenir=mysql_query("select codeindividu,nom,prenom,email from individu where codeindividu=".GetSQLValueString($row_rs_etudiant['codegesttheme'], "text")) or die(mysql_error());
		if($row_rs_acteur_du_role_a_prevenir=mysql_fetch_assoc($rs_acteur_du_role_a_prevenir))
		{ $tab_destinataires[$row_rs_acteur_du_role_a_prevenir['codeindividu']]=array('prenomnom'=>$row_rs_acteur_du_role_a_prevenir['prenom'].' '.$row_rs_acteur_du_role_a_prevenir['nom'],'email'=>$row_rs_acteur_du_role_a_prevenir['email']);
		}
		/* }
		else
		{ */ $rs_acteur_du_role_a_prevenir=mysql_query("select individu.codeindividu,nom,prenom,email from individu,structureindividu,structure".
																								" where individu.codeindividu=structureindividu.codeindividu".
																								" and structureindividu.codestructure=structure.codestructure".
																								" and codelib=".GetSQLValueString('srh', "text")) or die(mysql_error());
		/* } */
		if($row_rs_acteur_du_role_a_prevenir=mysql_fetch_assoc($rs_acteur_du_role_a_prevenir))
		{ $tab_destinataires[$row_rs_acteur_du_role_a_prevenir['codeindividu']]=array('prenomnom'=>$row_rs_acteur_du_role_a_prevenir['prenom'].' '.$row_rs_acteur_du_role_a_prevenir['nom'],'email'=>$row_rs_acteur_du_role_a_prevenir['email']);
		}
	}
	
	// contenu du message de validation
	$message.="Bonjour,<br><br>";
	$message.="Le sujet suivant".($coderole_a_prevenir==''?"":", affect&eacute; &agrave; ".$row_rs_etudiant['prenom']." ".$row_rs_etudiant['nom'].",")." a &eacute;t&eacute; ".(($row_rs_sujet['codestatutsujet']=="E")?"enregistr&eacute;":($row_rs_sujet['codestatutsujet']=="V"?"valid&eacute;":($row_rs_sujet['codestatutsujet']=="P"?"pass&eacute; a l'&eacute;tat pourvu":"")))." sur le serveur 12+ par ".$tab_infouser['prenom']." ".$tab_infouser['nom']." :";
	$message.="<br><br>Num&eacute;ro de sujet : ".$codesujet;
	$message.="<br>Type de sujet : ".$row_rs_sujet['libtypesujet'].($row_rs_sujet['codetypestage']!=''?" - ".$row_rs_sujet['libtypestage']:"")." (".aaaammjj2jjmmaaaa($row_rs_sujet['datedeb_sujet'],"/")." - ".aaaammjj2jjmmaaaa($row_rs_sujet['datefin_sujet'],"/").")";
	$message.="<br><br>Directeur(s) membre(s) du ".$GLOBALS['acronymelabo']." : ";
	
	mysql_data_seek($rs_dir,0);
	while($row_rs_dir=mysql_fetch_array($rs_dir))
	{ $message.=$row_rs_dir['prenom']." ".$row_rs_dir['nom'];
		$message.=" ";
	}
	if($row_rs_sujet['autredir1']!="")
	{ $message.="<br>Autre(s) Directeur(s) : ".$row_rs_sujet['autredir1']." ".$row_rs_sujet['autredir2'];
	}
	
	$message.="<br><br>".$GLOBALS['liblong_theme_fr']."(s) : ";
	$first=true;
	foreach($tab_theme as $key=>$libtheme)
	{ $message.=($first?"":", ").$libtheme;
		$first=false;
	}
	$message.="<br>Titre en fran&ccedil;ais : ".$row_rs_sujet['titre_fr'];
	$message.="<br>Description en fran&ccedil;ais : ".$row_rs_sujet['descr_fr'];
	if($row_rs_sujet['codetypesujet']!='02' || ($row_rs_sujet['codetypesujet']=='02' && $row_rs_sujet['codelibtypestage']=='MASTER'))
	{	$message.="<br>Mots cl&eacute;s fran&ccedil;ais : ".$row_rs_sujet['motscles_fr'];
		$message.="<br>Financement fran&ccedil;ais : ".$row_rs_sujet['financement_fr'];
		
		$message.="<br>Titre en anglais : ".$row_rs_sujet['titre_en'];
		$message.="<br>Description en anglais : ".$row_rs_sujet['descr_en'];
		$message.="<br>Mots cl&eacute;s anglais : ".$row_rs_sujet['motscles_en'];
		$message.="<br>Financement anglais : ".$row_rs_sujet['financement_en'];
		$message.="<br>R&eacute;f&eacute;rences de publications : ".$row_rs_sujet['ref_publis'];
	}
	if($row_rs_sujet['codestatutsujet']=="E")
	{ $message.="<br><br>";
		$message.="Ce sujet est actuellement 'En cours de validation' : la personne l'ayant propos&eacute; ne peut plus le modifier.";
		$message.="<br><br>";
		$message.="Connectez-vous au serveur 12+ afin de le VALIDER."; 
		
		$subject="Nouvelle proposition de sujet".($coderole_a_prevenir!=''?' ('.$row_rs_etudiant['prenom'].' '.$row_rs_etudiant['nom'].') ':'');
	}
	else if($row_rs_sujet['codestatutsujet']=="V")
	{ if($row_rs_sujet['codetypesujet']!='05')
		{ if($row_rs_sujet['afficher_sujet_web']=='oui')
			{ $message.="<br><br>Ce sujet appara&icirc;t en zone publique du serveur Web ".$GLOBALS['acronymelabo']." dans la liste des sujets ".($sujetaffecte?"'pourvus'":"'propos&eacute;s'").".";
			}
			else
			{ $message.="<br><br>Quand l&rsquo;affichage public sera valid&eacute;, ce sujet appara&icirc;tra en zone publique du serveur Web ".$GLOBALS['acronymelabo'].".";
			}
		}
		//$message.="<br><br>Ce sujet appara&icirc;t d&eacute;sormais en zone publique du serveur Web ".$GLOBALS['acronymelabo']." dans la liste des sujets 'pourvus'";
		$subject="Pour information : validation de sujet".($coderole_a_prevenir!=''?' ('.$row_rs_etudiant['prenom'].' '.$row_rs_etudiant['nom'].') ':'');
	}
	
	$message.="<br><br>";
	$message.="cordialement,";
	$message.="<br><br>";
	$message.="Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";			
	$message.="<br><br>";
	$message=html_entity_decode($message);
	
	$subject=	html_entity_decode($subject);

	$from = $GLOBALS['Serveur12+']['nom'].' <'.$GLOBALS['Serveur12+']['email'].'>';
	$replyto= $GLOBALS['Serveur12+']['nom'].' <'.$GLOBALS['Serveur12+']['email'].'>';
	
	$to="";
	$first=true;
	foreach($tab_destinataires as $un_destinataire=>$tab_un_destinataire)
	{ if(!array_key_exists(strtolower($tab_un_destinataire['email']),$tab_mail_unique))
		{ $tab_mail_unique[strtolower($tab_un_destinataire['email'])]=$tab_un_destinataire['email'];
			$to.=($first?"":", ").$tab_un_destinataire['prenomnom'].' <'.$tab_un_destinataire['email'].'>';
			$first=false;
		}
	}	
	//le user expediteur s'il n'est pas deja dans $to
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}
	
	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}

	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto, 'Subject' => $subject);
 //--------------- modifs pour mime
	//$text = $message;
	$message=nl2br($message);
	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime( "\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);
	$erreur=""; 
	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message);
	}
	else
	{ $erreur=$subject.'<br>'.$message;
	}
	//$erreur=$message;
	if(isset($rs_acteur_du_role_a_prevenir))mysql_free_result($rs_acteur_du_role_a_prevenir);
	if(isset($rs_etudiant))mysql_free_result($rs_etudiant);
	if(isset($rs_dir))mysql_free_result($rs_dir);
	if(isset($rs_theme))mysql_free_result($rs_theme);
	if(isset($rs_sujet))mysql_free_result($rs_sujet);
	
	return $erreur;
}
/* pour version gestionsujets avec affectation possible a etudiant apres visa dept appose
function mail_affectation_sujet($codesujet,$tab_infouser)
{ $sujetaffecte=false;
	$message='';
	$tab_destinataires=array();// destinataires : pas de doublon car ecrasement par $tab_destinataires[$....['codeindividu']]
	$tab_mail_unique=array();//evite d'avoir deux fois le meme destinataire (meme adresse mail) dans le champ To:
	$tab_theme=array();
	$rs_sujet=mysql_query("select sujet.*,".
												" typesujet.libcourt_fr as libtypesujet,libstatutsujet,codelibtypestage,libcourttypestage as libtypestage".
												" from sujet,typesujet,statutsujet,typestage".
												" where sujet.codesujet=".GetSQLValueString($codesujet, "text").
												" and sujet.codetypesujet=typesujet.codetypesujet".
												" and sujet.codestatutsujet=statutsujet.codestatutsujet and sujet.codetypestage=typestage.codetypestage") or die(mysql_error());
	$row_rs_sujet=mysql_fetch_assoc($rs_sujet);
	// expediteur
	$tab_destinataires[$tab_infouser['codeindividu']]=array('prenomnom'=>$tab_infouser['prenom'].' '.$tab_infouser['nom'],'email'=>$tab_infouser['email']);
	// les encadrants
	$rs_dir=mysql_query("select individu.codeindividu,nom,prenom,email from sujetdir,individu ".
											" where sujetdir.codesujet=".GetSQLValueString($codesujet, "text").
											" and sujetdir.codedir=individu.codeindividu ".
											" order by numordre") or die(mysql_error());
	while($row_rs_dir=mysql_fetch_array($rs_dir))
	{ $tab_destinataires[$row_rs_dir['codeindividu']]=array('prenomnom'=>$row_rs_dir['prenom'].' '.$row_rs_dir['nom'],'email'=>$row_rs_dir['email']);
	}
												
	// gestionnaire de theme et SRH
	$rs_etudiant=mysql_query(	"select individu.codeindividu,nom,prenom,codegesttheme from individu,individusejour,individusujet ".
														" where individu.codeindividu=individusejour.codeindividu".
														" and individusejour.codeindividu=individusujet.codeindividu and individusejour.numsejour=individusujet.numsejour".
														" and individusujet.codesujet=".GetSQLValueString($codesujet, "text")) or die(mysql_error());
	$row_rs_etudiant=mysql_fetch_assoc($rs_etudiant);
	$rs_acteur_du_role_a_prevenir=mysql_query("select codeindividu,nom,prenom,email from individu where codeindividu=".GetSQLValueString($row_rs_etudiant['codegesttheme'], "text")) or die(mysql_error());
	if($row_rs_acteur_du_role_a_prevenir=mysql_fetch_assoc($rs_acteur_du_role_a_prevenir))
	{ $tab_destinataires[$row_rs_acteur_du_role_a_prevenir['codeindividu']]=array('prenomnom'=>$row_rs_acteur_du_role_a_prevenir['prenom'].' '.$row_rs_acteur_du_role_a_prevenir['nom'],'email'=>$row_rs_acteur_du_role_a_prevenir['email']);
	}
	$rs_acteur_du_role_a_prevenir=mysql_query("select individu.codeindividu,nom,prenom,email from individu,structureindividu,structure".
																							" where individu.codeindividu=structureindividu.codeindividu".
																							" and structureindividu.codestructure=structure.codestructure".
																							" and codelib=".GetSQLValueString('srh', "text")) or die(mysql_error());
	$row_rs_acteur_du_role_a_prevenir=mysql_fetch_assoc($rs_acteur_du_role_a_prevenir);
	$tab_destinataires[$row_rs_acteur_du_role_a_prevenir['codeindividu']]=array('prenomnom'=>$row_rs_acteur_du_role_a_prevenir['prenom'].' '.$row_rs_acteur_du_role_a_prevenir['nom'],'email'=>$row_rs_acteur_du_role_a_prevenir['email']);
	
	$subject="Pour information : affectation de sujet".$row_rs_etudiant['prenom'].' '.$row_rs_etudiant['nom'];

	// contenu du message de validation
	$message.="Bonjour,<br><br>";
	$message.="Le sujet suivant a &eacute;t&eacute; affect&eacute; &agrave; ".$row_rs_etudiant['prenom']." ".$row_rs_etudiant['nom']." sur le serveur 12+ par ".$tab_infouser['prenom']." ".$tab_infouser['nom'];
	$message.="<br><br>Num&eacute;ro de sujet : ".$codesujet;
	$message.="<br>Type de sujet : ".$row_rs_sujet['libtypesujet'].($row_rs_sujet['codetypestage']!=''?" - ".$row_rs_sujet['libtypestage']:"")." (".aaaammjj2jjmmaaaa($row_rs_sujet['datedeb_sujet'],"/")." - ".aaaammjj2jjmmaaaa($row_rs_sujet['datefin_sujet'],"/").")";
	$message.="<br><br>Directeur(s) membre(s) du ".$GLOBALS['acronymelabo']." : ";
	
	mysql_data_seek($rs_dir,0);
	while($row_rs_dir=mysql_fetch_array($rs_dir))
	{ $message.=$row_rs_dir['prenom']." ".$row_rs_dir['nom'];
		$message.=" ";
	}
	if($row_rs_sujet['autredir1']!="")
	{ $message.="<br>Autre(s) Directeur(s) : ".$row_rs_sujet['autredir1']." ".$row_rs_sujet['autredir2'];
	}
	
	$message.="<br><br>".$GLOBALS['liblong_theme_fr']."(s) : ";
	$message.="<br>Titre en fran&ccedil;ais : ".$row_rs_sujet['titre_fr'];
	
	$message.="<br><br>";
	$message.="cordialement,";
	$message.="<br><br>";
	$message.="Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";			
	$message.="<br><br>";
	$message=html_entity_decode($message);
	
	$subject=	html_entity_decode($subject);

	$from = $GLOBALS['Serveur12+']['nom'].' <'.$GLOBALS['Serveur12+']['email'].'>';
	$replyto= $GLOBALS['Serveur12+']['nom'].' <'.$GLOBALS['Serveur12+']['email'].'>';
	
	$to="";
	$first=true;

	foreach($tab_destinataires as $un_destinataire=>$tab_un_destinataire)
	{ if(!array_key_exists(strtolower($tab_un_destinataire['email']),$tab_mail_unique))
		{ $tab_mail_unique[strtolower($tab_un_destinataire['email'])]=$tab_un_destinataire['email'];
			$to.=($first?"":", ").$tab_un_destinataire['prenomnom'].' <'.$tab_un_destinataire['email'].'>';
			$first=false;
		}
	}	
	//le user expediteur s'il n'est pas deja dans $to
	if(!array_key_exists(strtolower($tab_infouser['email']),$tab_mail_unique) && est_mail($tab_infouser['email']))
	{ $to.=($to==""?"":", ").$tab_infouser['prenom']." ".$tab_infouser['nom']." <".$tab_infouser['email'].">";
	}
	// le développeur
	if(!array_key_exists(strtolower($GLOBALS['webMaster']['email']),$tab_mail_unique))
	{ $to.=($to==""?"":", ").$GLOBALS['webMaster']['nom'].' <'.$GLOBALS['webMaster']['email'].'>';
	}
	
	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}

	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto, 'Subject' => $subject);
 //--------------- modifs pour mime
	//$text = $message;
	$message=nl2br($message);
	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime( "\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);
	$erreur=""; 
	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message);
	}
	else
	{ $erreur=$subject.'<br>'.$message;
	}
	//$erreur=$message;
	if(isset($rs_acteur_du_role_a_prevenir))mysql_free_result($rs_acteur_du_role_a_prevenir);
	if(isset($rs_etudiant))mysql_free_result($rs_etudiant);
	if(isset($rs_dir))mysql_free_result($rs_dir);
	if(isset($rs_theme))mysql_free_result($rs_theme);
	if(isset($rs_sujet))mysql_free_result($rs_sujet);
	
	return $erreur;
}
 */
function popup_validation_projet($typevalidation,$codeprojet,$tab_infouser)
{ $message="";
	$query_rs="select structure.codelib as codelibtheme from projet,structure".
						" where projet.codetheme=structure.codestructure".
						" and projet.codeprojet=".GetSQLValueString($codeprojet, "text");
	$rs=mysql_query($query_rs) or die(mysql_error());
	$row_rs=mysql_fetch_assoc($rs);
	$codelibtheme=$row_rs['codelibtheme']; 	

	if($typevalidation=='brouillon')
	{ $message= addslashes("Le sujet ne sera plus visible par les autres membres");
	}
	else
	{ $message= addslashes("Un message de publication de ce projet va &ecirc;tre adress&eacute; &agrave; la liste cran-".$codelibtheme)."\\n".
							addslashes("et le sujet sera visible par l'ensemble de ses membres");
	}
  if(isset($rs))mysql_free_result($rs);
	return $message;
}

// mail envoye aux acteurs concernes du projet 
function mail_validation_projet($codeprojet,$tab_infouser)
{ $message="";
	$query_rs="select structure.codelib as codelibtheme from projet,structure".
						" where projet.codetheme=structure.codestructure".
						" and projet.codeprojet=".GetSQLValueString($codeprojet, "text");
	$rs=mysql_query($query_rs) or die(mysql_error());
	$row_rs=mysql_fetch_assoc($rs);
	$codelibtheme=$row_rs['codelibtheme']; 	
 	$rs_projet=mysql_query("select projet.*, cont_classif.libcourtclassif as libclassif  from projet, cont_classif".
												 " where projet.codeclassif=cont_classif.codeclassif and projet.codeprojet=".GetSQLValueString($codeprojet,"text")) or die(mysql_error());
	$row_rs_projet=mysql_fetch_assoc($rs_projet);
	$subject="Nouveau projet d&eacute;pos&eacute; par ".$tab_infouser['prenom']." ".$tab_infouser['nom'];
	// contenu du message de validation
	$message.="Message &agrave; l'attention des chercheurs, doctorants et post-doctorants du d&eacute;partement ".strtoupper($codelibtheme)."<br><br>";
	$message.="Bonjour,<br><br>";
	$message.="Le projet suivant a &eacute;t&eacute; d&eacute;pos&eacute; sur le serveur 12+ par ".$tab_infouser['prenom']." ".$tab_infouser['nom']." :";
	
	if($row_rs_projet['titrecourt']!='')
	{ $message.="<br>Intitul&eacute; court : ".$row_rs_projet['titrecourt'];
	}
	$message.="<br>Intitul&eacute; : ".$row_rs_projet['titre'];
	$message.="<br>Type de projet : ".$row_rs_projet['libclassif'];
	$message.="<br>Date : ".aaaammjj2jjmmaaaa($row_rs_projet['datedeb_projet'],"/");
	$message.="<br>Description : ".$row_rs_projet['descr'];
	
	
	$message.="<br><br>";
	$message.="cordialement,";
	$message.="<br><br>";
	$message.="Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";			
	$message.="<br><br>";
	$message=html_entity_decode($message);

	$subject=	html_entity_decode($subject);
	$from = $tab_infouser['prenom']." ".$tab_infouser['nom'].' <'.$tab_infouser['email'].'>';
	$replyto= $tab_infouser['prenom']." ".$tab_infouser['nom'].' <'.$tab_infouser['email'].'>';
	$to="cran-".$codelibtheme."@univ-lorraine.fr";

	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}
	
	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto, 'Subject' => $subject);
 //--------------- modifs pour mime
	//$text = $message;
	$message=nl2br($message);
	$message=html_entity_decode($message);
	$message=str_replace("images/",$GLOBALS['racine_site_web_labo']."images/",$message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	$mime = new Mail_mime( "\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);
	$erreur=""; 
	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message);
	}
	else
	{ $erreur=$subject.'<br>'.$message;
	}
	if(isset($rs))mysql_free_result($rs);
	if(isset($rs_projet))mysql_free_result($rs_projet);
	
	return $erreur;
}


function mail_validation_registre($tab_post)
{  $erreur="";
	// contenu du message de demande de validation
	$subject="Nouvelle observation dans le registre H&S";
	$message="
	Bonjour,\n\n
	Une nouvelle observation a &eacute;t&eacute; depos&eacute;e par ".$tab_post['nom']." dans le registre H&S du serveur 12+ :\n
	Lieu : ".$tab_post['lieu']."\n
	Fait constat&eacute; : ".$tab_post['fait']."\n
	Observations : ".$tab_post['observation']."\n
	Suggestions : ".$tab_post['suggestion']."\n\n
	cordialement,\n\n
	Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";
	$subject=	html_entity_decode($subject);
	
	$from = "Serveur 12+<".$GLOBALS['webMaster']['email'].">";
	$replyto="Serveur 12+<".$GLOBALS['webMaster']['email'].">";
	$to="DU<".$GLOBALS['emailDU'].">,ACMO<".$GLOBALS['emailACMO'].">";
	
	if($GLOBALS['mode_exploit']=='test')
	{	$message.='<br>En test, destinataires en fin de message : '.$to;
		$to="TEST <".$GLOBALS['emailTest'].">";
	}


	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto, 'Subject' => $subject);
	//--------------- modifs pour mime
	//$text = $message;
	$message=nl2br($message);
	$message=html_entity_decode($message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="http://vm-web-cran.cran.uhp-nancy.fr/cran_php/styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime( "\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	//$mime->addBcc('pascal.gend@wanadoo.fr');
	$headers = $mime->headers($headers);


	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message);
	}
	else
	{ $erreur='mode_avec_envoi_mail=false<br>'.$subject.'<br>'.$message;
	} /**/
	return $erreur;
}

// mail envoye aux acteurs concernes 
function popup_validation_actu($typevalidation,$codeactu,$tab_infouser)
{
}

function mail_validation_actu($codeactu,$tab_infouser,$coderole_a_prevenir)
{ /* $erreur="";
	// contenu du message de demande de validation
	$subject="Nouvelle observation dans le registre H&S";
	$message="
	Bonjour,\n\n
	Une nouvelle observation a &eacute;t&eacute; depos&eacute;e par ".$nom." dans le registre H&S du serveur CRAN :\n
	titre_fr : ".$titre_fr."\n
	texte_fr : ".$texte_fr."\n
	Observations : ".$observation."\n
	Suggestions : ".$suggestion."\n\n
	cordialement,\n\n
	Message g&eacute;n&eacute;r&eacute; automatiquement par le Serveur 12+";
	$subject=	html_entity_decode($subject);
	
	$from = $GLOBALS['Serveur12+']['nom']."<".$GLOBALS['Serveur12+']['email'].">";
	$replyto=$GLOBALS['Serveur12+']['nom']."<".$GLOBALS['webMaster']['email'].">";
	$to=$GLOBALS['webMaster']['email'];
	$headers = array ('From' => $from,'To' => $to,'Reply-To' => $replyto, 'Subject' => $subject);
	//--------------- modifs pour mime
	//$text = $message;
	$message=nl2br($message);
	$message=html_entity_decode($message);
	$html_message = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
	<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
	<title>....</title>
	<link rel="stylesheet" href="'.$GLOBALS['racine_site_web_labo'].'styles/normal.css">
	</head>
	<body>'.
	$message.'
	</body>
	</html>';
	//$mime->setTXTBody($text);Le texte est transformé en html : erreur de paramétrage meme avec 
	$mime = new Mail_mime( "\n");
	$mime->setHTMLBody($html_message);
	$mimeparams=array();  
	$mimeparams['text_encoding']="7bit";//par defaut
	$mimeparams['html_encoding']="quoted-printable";//par defaut
	$mimeparams['text_charset']="iso-8859-1";
	$mimeparams['html_charset']="iso-8859-1";
	$mimeparams['head_charset']="iso-8859-1";
	$message_html_txt = $mime->get($mimeparams);
	$headers = $mime->headers($headers);

	if($GLOBALS['mode_avec_envoi_mail'])
	{ $erreur=envoimail($headers, $message);
	}
	else
	{ $erreur=$subject.'<br>'.$message;
	} */
	return $erreur;
}
function envoimail($headers, $message)
{ //$smtpserver = "smtp.uhp-nancy.fr";
	$smtpserver = $GLOBALS['smtpserver'];
	$smtp = Mail::factory('smtp',array ('host' => $GLOBALS['smtpserver'],/*'port' => $GLOBALS['smtpport'],*/"localhost"=>"VM-WEB-CRAN.cran.uhp-nancy.fr"));
	$resmail=$smtp->send($headers['To'], $headers, $message);
	if(PEAR::isError($resmail))
	{ return $resmail;
	}
	else
	{ return "";
	}
}

function affiche_longueur_js($champ,$longueurmax,$champaffichage,$class_si_ok,$class_si_pasok)
{ $texte="";
  foreach(array("onKeyDown","onKeyUp","onMouseUp","onMouseDown") as $event)
	{ $texte.=$event."=\"affiche_longueur(".$champ.",".$longueurmax.",".$champaffichage.",".$class_si_ok.",".$class_si_pasok.")\" ";
	}
	return $texte;
}
function bandeausup($codeuser)
{
}

function enregistrer_form($prog_courant)
{ // on verifie que l'appel provient du programme courant (pas d'un autre) et que l'occurence du formulaire egale celle de la variable
  // de session compteur pour ce programme: si l'occurence du formulaire est plus petite que celle de la variable de session, c'est qu'on a fait des 
  // retours arriere avec les fleches de navig.
	// $_SESSION['prog_appel']=nom du programme d'appel,$_SESSION[$prog_courant]=compteur du $prog_courant 
  $enregistrer_form=false;
	$txt_enregistrer_form="";
	if(isset($_SESSION['prog_appel']))
  { if($_SESSION['prog_appel']==$prog_courant)
		{ $txt_enregistrer_form="<br>_SESSION['prog_appel']=".$prog_courant."==".$prog_courant." : true";//true;
			$enregistrer_form=true;
		}
		else
		{ $txt_enregistrer_form="<br><br>_SESSION['prog_appel']<>prog_courant : false";//$enregistrer_form=false;
			$enregistrer_form=false;
		}
	}
  if(isset($_SESSION[$prog_courant]))
  { if($_SESSION[$prog_courant]==$_POST[$prog_courant])//compteurs egaux
    { $txt_enregistrer_form.="<br><br>Compteur : _SESSION[".$prog_courant."]=".$_SESSION[$prog_courant]." =_POST[".$prog_courant."] : true";//true;
			$enregistrer_form=true;
		}
		else
		{ $txt_enregistrer_form.="<br><br>Compteur : _SESSION[".$prog_courant."]".$_SESSION[$prog_courant]."<>_POST[".$prog_courant."] : false";//false;
			$enregistrer_form=false;
		}
    $_SESSION[$prog_courant]++;
  }
  else
  { $_SESSION[$prog_courant]=1;
  }
  $_SESSION['prog_appel']=$prog_courant;
	$txt_enregistrer_form.="<br>_SESSION[".$prog_courant."]".$_SESSION[$prog_courant];
	$txt_enregistrer_form.="<br>_SESSION['prog_appel']=".$_SESSION['prog_appel'];
  return array('txt_enregistrer_form'=>$txt_enregistrer_form,'bool_enregistrer_form'=>$enregistrer_form);
}


