<?php
$racine_site_web_cran="http://www.cran.univ-lorraine.fr/";
$charset='charset=iso-8859-1';
$emailDU='didier.wolf@univ-lorraine.fr';
$emailACMO='cran-acmo@univ-lorraine.fr';
$webMasterMail = "pascal.gend@univ-lorraine.fr";
//*********************************** A modifier sur site en exploitation
$mode_exploit="test";
//$mode_exploit="normal";
//$mode_exploit="restreint";
$mode_envoi_mail_valide_sujet=true;
$mode_envoi_mail_valide_individu=true;
$siteouvert=true;
//$siteouvert=false;
$display_errors=true;
//$display_errors=false;
$GLOBALS['rep_racine_monsite']='crantest_php';
$GLOBALS['date_deb_12plus_budget']='2013/01/01';
$GLOBALS['date_deb_exercice_comptable']='2014/01/01';
$GLOBALS['date_fin_exercice_comptable']='2014/12/31';
//********************************** Pas de modif
$GLOBALS['suffixe_dotation_01']='';
$GLOBALS['suffixe_dotation_02']='RSA -- LDDIR';
//message de bienvenue
$affiche_12plus_bonjour='affiche_12plus_bonjour.jpg';
$GLOBALS['sitefermemotif']="Le site est ferm&eacute; jusqu&rsquo;au lundi 13 janvier 2014 - 9h pour raison de maintenance. Veuillez nous en excuser.";
$GLOBALS['sitebonjour']="<center><img src='images/galerie/".$affiche_12plus_bonjour."'></center>";
$GLOBALS['siteaurevoir']="<center><img src='images/galerie/affiche_12plus_aurevoir.jpg'></center>";
$GLOBALS['siteloginerreur']="<center><img src='images/galerie/affiche_12plus_loginerreur.jpg'></center>";
$GLOBALS['webMaster'] = array('nom'=>'WebMaster','email'=>'pascal.gend@univ-lorraine.fr');
$GLOBALS['Serveur12+'] = array('nom'=>'Serveur 12+','email'=>'Didier.Wolf@univ-lorraine.fr');
$GLOBALS['ServeurCRAN'] = array('nom'=>'Serveur du CRAN','email'=>'Didier.Wolf@univ-lorraine.fr');
$GLOBALS['Serveur12+commande'] = array('nom'=>'serveur 12+','lien'=>'http://195.220.155.4/'.$GLOBALS['rep_racine_monsite'].'/formintranetpasswd.php','emailexpediteur'=>'Didier.Wolf@univ-lorraine.fr','emailretour'=>'Carole.Courrier@univ-lorraine.fr');
$GLOBALS['assurancemission_contact_ul'] = array('prenomnom'=>'Thierry COURTOIS','email'=>"thierry.courtois@univ-lorraine.fr");
$GLOBALS['smtpserver'] = "smtp-int.univ-lorraine.fr";//"mx-2.mail.uhp-nancy.fr";//"smtps.uhp-nancy.fr";
$GLOBALS['smtpport'] = "25";//"587";
$GLOBALS['urlsic']='http://sic.cran.uhp-nancy.fr';
	
$GLOBALS['mode_exploit']=$mode_exploit;
$GLOBALS['racine_site_web_cran']=$racine_site_web_cran;

$GLOBALS['tab_car_accent_maj_transforme']=array("&Agrave;"=>"A","&Eacute;"=>"E","&Egrave;"=>"E","&Ecirc;"=>"E","&Icirc;"=>"I",
																					"&Ocirc;"=>"O","&Uacute;"=>"U","&Ugrave;"=>"U","&Ucirc;"=>"U");
$GLOBALS['max_file_size']=pow(2,23);//8  Mo
$GLOBALS['max_file_size_Mo']=8;//2
// types de fichiers uploades : penser a reporter dans alert.js
$GLOBALS['file_types_array']=array('pdf','doc','docx','txt','xls','xlsx','csv','gif','jpeg','jpg','png');
$GLOBALS['file_types_mime_array']=array('pdf'=>'application/pdf','doc'=>'application/msword','docx'=>'application/msword','txt'=>'application/text','xls'=>'application/vnd.ms-excel','xlsx'=>'application/vnd.ms-excel',
'csv'=>'application/vnd.ms-excel','gif'=>'image/gif','jpeg'=>'image/jpeg','jpg'=>'image/jpeg','png'=>'image/png');
$GLOBALS['tab_erreur_upload']=array( UPLOAD_ERR_OK=>'',
																		 UPLOAD_ERR_INI_SIZE=>	'Le fichier t&eacute;l&eacute;charg&eacute; exc&egrave;de la taille maximale autoris&eacute;e par le syst&egrave;me.' ,
																		 UPLOAD_ERR_FORM_SIZE=>	'Le fichier t&eacute;l&eacute;charg&eacute; exc&egrave;de la taille maximale autoris&eacute;e ('.$GLOBALS['max_file_size_Mo'].' Mo).',
																		 UPLOAD_ERR_PARTIAL=>		'Le fichier n&rsquo;a &eacute;t&eacute; que partiellement t&eacute;l&eacute;charg&eacute;.', 
																		 UPLOAD_ERR_NO_FILE=>		'Aucun fichier n&rsquo;a &eacute;t&eacute; t&eacute;l&eacute;charg&eacute;.', 
																		 UPLOAD_ERR_NO_TMP_DIR=>'Un dossier temporaire est manquant.',
																		 UPLOAD_ERR_CANT_WRITE=>'Echec de l&rsquo;&eacute;criture du fichier sur le disque : erreur syst&eacute;.',
																		 UPLOAD_ERR_EXTENSION=>	'L&rsquo;extension n&rsquo;est pas autoris&eacute;e ('.implode(", ", $GLOBALS['file_types_array']).').'
																		);
$GLOBALS['date_limite_affiche_champ_prog_rech']='2012/09/01';
$GLOBALS['date_bascule_gt_vers_dept']='2013/01/01';
if(date('Y/m/d')<$GLOBALS['date_bascule_gt_vers_dept'])
{ $GLOBALS['libcourt_theme_fr']='GT/Dept';
  $GLOBALS['liblong_theme_fr']='Groupe thématique/Département';
}
else
{ $GLOBALS['libcourt_theme_fr']='Dept.';
  $GLOBALS['liblong_theme_fr']='Département';
}

?>