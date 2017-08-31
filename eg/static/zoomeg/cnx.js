/* -----------------------------------------------------------------------
cnx est une librairie javascript JSON d�velopp�e par jpconnexion et claudecnx

Copyright et r�gles d'utilisation:
L'utilisation de ce code ou d�riv� est soumis � notre accord: claudecnx@blanquefort.net
Merci de laisser ces lignes, nous proposer toutes �volutions de code que vous pouvez apporter

Pour utiliser ce fichier:
<script src="http://jpconnexion.free.fr/script2012/cnx.js"></script>
En localhost faire:

<script src="../2012script/cnx.js"></script>
----------------------------------------------------------------------- */
(function() { //anonyme fonction
	cnx = (function() { /** ne pas utiliser var pour d�finir cnx  */
			/* private section */
			return { /** public section */
				version: "cnx version: 2012-04-05",
				author: "jpc claude cnx",
					
				trace: (function() { //fonction anonyme - mode debugger et tra�age
						// private section
						var id_div = (arguments[0]) ?  arguments[0] : "id_print";; //r�cup�re le premier param�tre ou si vide "id_print" - id de la div associ�e
						var objetDiv; //il faut le d�finir en dehors de la fonction init() pour �tre accessible dans la public section
						var init = function(){ //private section - initialise la div si elle n'existe pas d�j�!
							/* -----------------
							cr�er la div si elle n'existe pas
							initialise objetDiv
							---------- */
							objetDiv=document.getElementById(id_div);//teste si la <div> existe
							if (objetDiv == null) { //cr�er la <div> si elle n'existe pas d�j�
								objetDiv = document.createElement("div");
								objetDiv.id = id_div;
								objetDiv.style.position = "absolute";
								objetDiv.style.left = "900px";
								objetDiv.style.top="200px";
								objetDiv.style.width = "500px"; //dimensionne la <div>
								objetDiv.style.height= "250px"; //dimensionne la <div>
								objetDiv.style.overflow= "scroll"; //ajoute les ascenseurs
								objetDiv.style.visibility = "hidden";
								cnx.dom().appendTo(document.body, objetDiv); //document.body.appendChild(objetDiv);
							}
						};
						//end of private section
						return { //public section
							print: function(str_print){
								/* ----------------------------------------
								code de la div asoci�e:
								<div  id="id_print" style="visibility:hidden; ">Surveillance et d�boggage</div> 
					
								cnx.trace.debug = true; //ne s'affiche que si cnx.trace.debug = true
								cnx.trace().print(data);
								----------------------------------------- */
								init(); //cr�er la div si elle n'existe pas
								if (cnx.trace.debug){ //ne s'affiche que si debug est vrai!
									objetDiv.style.visibility="visible"; //rend visible la <div> automatiquement
									var ecriture = objetDiv.innerHTML;
									ecriture = str_print + "<BR>" + ecriture;
									objetDiv.innerHTML = ecriture;
								} else objetDiv.style.visibility = "hidden";
							},
							setTop: function(str_value){
								cnx.trace().init(); //cr�er la div si elle n'existe pas
								cnx.style().setTop(str_value, objetDiv);
							},
							debug: false //cnx.trace.debug = true;	 pour afficher; ne sert � rien ici, m�morisation du process!
							
						}; //end of return
				}), //end of trace() - la fonction anonyme n'est pas en auto ex�cution, elle admet des param�tres
			
				file: (function() { //gestion de fichier
					/* private section */
					return {
						searchExtension: function(chaine){ //	{{{
							var extension = chaine.substring(chaine.lastIndexOf("."));
							if (extension == -1)	extension = false; //retourne -1 si rien trouv�! pour m�moire -1 est diff�rent de false
							return extension; 
						}, //	}}}
					
						include: function (){	//ajoute un fichier js ou css	{{{
							if (!document.getElementById)	return;
							for (i=0; i<arguments.length; i++){
								var str_fullFileName=arguments[i];
								var extension = cnx.file.searchExtension(str_fullFileName);
								if (extension == ".js"){ //Inclusion d'un fichier javascript
									var js_script = document.createElement("script");
									js_script.type = "text/javascript"; //js_script.setAttribute("type", "text/javascript");
									js_script.src = str_fullFileName; //js_script.setAttribute("src", str_fullFileName);
									document.getElementsByTagName("head")[0].appendChild(js_script); //document.getElementsByTagName("head").item(0).appendChild(js_script);
								}
								if (extension == ".css"){ //Inclusion d'une feuille de style css
									var css_style=document.createElement("link");
									css_cnx.setAttribute("rel", "stylesheet"); //css_cnx.rel = 'stylesheet';
									css_cnx.setAttribute("type", "text/css"); //css_cnx.type = 'text/css';
									css_cnx.setAttribute("href", str_fullFileName); //css_cnx.href = '../jpclibrary_script/slider.css';
									css_cnx.setAttribute("media", "screen"); //css_cnx.media = 'screen';
									document.getElementsByTagName("head")[0].appendChild(css_style);
								}
							}
						},	//	}}}
						
						isloadedCSS: function (stringFileCSS){	//	{{{
							/* -------------------------------------------------------------
							v�rifie si un fichier CSS est charg�
							Parcours l'ensemble des fichiers CSS charg�
							Pour chacun des fichier CSS v�rifie que les r�gles CSS sont bien pr�sentes
							si le nombre de r�gles CSS = 0 le fichier n'est pas charg� ou ne contient aucun r�gle CSS, fichier vide!
							Ne g�re pas les fichier CSS @import
							------------------------------------------ */
							var ie = document.all;
							var loading = false;
							for ( i = 0; i < document.styleSheets.length; i++ ){ //parcours tous les fichiers CSS charg�s
								var fullfilenameCSS = document.styleSheets[i].href; //href retourne le chemin complet du fichier CSS
								if (isNotNull(fullfilenameCSS)){ //test si Null car @import retourne Null
									if (fullfilenameCSS.indexOf(stringFileCSS) > 0){ //si fullfilenameCSS contient stringFileCSS: le chemin complet contient le fichier CSS recherch�
										//nota: indexOf() retourne -1 si la chaine recherch�e (stringFileCSS) n'est pas contenue dans la chaine initiale (fullfilenameCSS)
										var nbr_reglesCSS = (ie)? document.styleSheets[i].rules.length : document.styleSheets[i].cssRules.length; //notation pour firefox, opera...
										if (nbr_reglesCSS > 0) loading = true; //si le fichier n'existe pas ou est vide ou ne contient que du commentaire, le nombre de rgle CSS = 0
									}
								}
							}
							if (!loading) alert('Style '+stringFileCSS+' non charg�e!\n Ins�rer la ligne: \n <link rel="stylesheet" href="../jpclibrary_script/'+stringFileCSS+'"> \n Et v�rifier le chemin.');
							return loading; //true si charg� avec ces r�gles CSS, autremant false
						},	//	}}}
						
						isloadedjs: function (string_variable, stringfichier){	//teste si un fichier javascript est charg�	{{{
							var string_error_msg = ' \n Classe '+stringfichier+' non charg�e!\n Ins�rer la ligne: \n <script src="../jpclibrary_script/'+stringfichier+'"></script> \n Et v�rifier le chemin.';
							isDefined(string_variable, string_error_msg, false);
						}
					}; //end of return
				}), // end of classe - cnx.file().searchExtension()
			
				dom: (function() { //fonction anonyme - gestion du DOM et nodes �l�ments
						/* private section */
						return { //public section
							appendTo: function(parent, child){	// ajoute un enfant � un parent
								
								/* ----------------------------
								Ajoute un �l�ment enfant (child) � un �l�ment parent
								this.parent = (this.parent)? this.parent: document.body;
								cnx.dom().appendTo(document.body, enfant);
								----------------------------- */
								parent.appendChild(child);
							},
							
							removeElt: function (elt){ //d�truit un �l�ment
								var elt = cnx.dom().getElt(elt); //accepte id ou object, renvoie false si elt n'existe pas
								if (!elt) return false; // si elt n'existe pas retourne false
								var parent = cnx.dom().nodeParent(elt); //recherche le parent
								parent.removeChild(elt); //retire l'enfant, donc le d�truit
								/*
								for (prop in elt){
									prop = null;
								}
								elt = null;
								*/
								return true;
							},
							
							listeProp: function (elt){ //lit et affiche toutes les propri�t�s d'un �l�ment HTML
								var elt = cnx.dom().getElt(elt); //si elt est id, retourne objet HTML associ�
								for (prop in elt) {
									document.write("Propri�t� : " + prop + " -> " + elt[prop] + "<br>");
								} 
								return false;
							},
							
							changeId: function(ancienID, newID){	// modifie l'id d'un �l�ment
								var elt = document.getElementById(ancienID);
								if (isNotNull(elt)) {
									elt.id = newID;
									var retour = true;
								} else var retour= false;
								return retour;
							},
								
							getNodeInfo: function(elt, tagName) { //affiche des informations choisies sur un elt et ses enfants
								/* 
								cnx.dom().getChildNodes(document); //liste toute la page html mais c'est long! 
								cnx.dom().getChildNodes("identificateur"); //liste les informations de l'objet ayant pour id = "identificateur"
								cnx.dom().getChildNodes("identificateur", "INPUT"); //liste toutes les balises <INPUT> contenues dans elt
								*/
								elt = cnx.dom().getElt(elt); //si id transmit trouve elt associ�
								if (!tagName) tagName = false; //si tagName n'existe pas tagName = false
								var Container = "Object Container: "+elt.nodeName +" / "+elt;
								var Identifiant = "\n has for id : " + elt.id;
								var Parent;
								(cnx.dom().nodeParent(elt)) ? Parent = "\n has for Parent: "+cnx.dom().nodeParent(elt).nodeName + " / "+ cnx.dom().nodeParent(elt) : Parent = "\n #document has no Parent";
								var GrandParent;
								(dom.nodeParent(elt, 2)) ? GrandParent = "\n has for Grand-Parent: "+cnx.dom().nodeParent(elt, 2).nodeName + " / "+ cnx.dom().nodeParent(elt, 2) :GrandParent = "\n  has not Grand-Parent";
								var Children = "\n has " +cnx.dom().nodeChild(elt) +" children";
								var Attributs = "\n has "+ cnx.dom().nodeAttributes(elt)+" attributes : " ;
								//var Attribut2s = "\n has "+ cnx.dom().nodeProp(elt)+" Propri�t�s : " ;
								var Type = "\n is type : " + cnx.dom().nodeType(elt) + " / " + elt.nodeType;
								var Contents = "\n it's contents : " + cnx.dom().nodeContents(elt);
								
								if (!tagName)	alert(Container+Identifiant+Parent+GrandParent+Children+Attributs+Type+Contents + "\n Search Mode: all Tag"); //liste tous les elt si tagName est faux
						
								if( (tagName) && (tagName.toLowerCase() == elt.nodeName.toLowerCase() ) ){ //ne liste que les elt correspondant � la balise
									alert(Container+Identifiant+Parent+GrandParent+Children+Attributs+Type+Contents + "\n Search in Tag : " + elt.nodeName); 
								} 
						
						
								for (var i = 0; i < elt.childNodes.length; i++) { //cherche les enfants
										var child = elt.childNodes[i]; //liste les enfants
										cnx.dom().getNodeInfo(child, tagName); //appel r�curssif pour chaque enfant du node
								}
								return elt.childNodes.length; // retourne le nombre d'enfants pour listage �ventuel
						
							}, 
							
							nodeContents: function(elt){// retourne le contenu d'un �l�ment
								if (cnx.log().isString(elt))	elt = document.getElementById(elt); // si String cherche �l�ment objet
								var contents;
								switch(elt.nodeType){
								case 1: //ELEMENT_NODE
									contents = elt.innerHTML;
									break;
								case 2:
									//contents = "ATTRIBUTE_NODE";
									break;
								case 3: //TEXT_NODE
									contents=elt.data;
									break;
								case 4:
									//contents="CDATA_SECTION_NODE";
									break;
								case 5:
									//contents="ENTITY_REFERENCE_NODE";
									break;
								case 6:
									//contents="ENTITY_NODE";
									break;
								case 7:
									//contents="PROCESSING_INSTRUCTION_NODE";
									break;
								case 8:
									//contents="COMMENT_NODE";
									break;
								case 9:
									//contents="DOCUMENT_NODE";
									break;
								case 10:
									//contents="DOCUMENT_TYPE_NODE"
									break;
								case 11:
									//contents="DOCUMENT_FRAGMENT_NODE";
									break;
								case 12:
									//contents="NOTATION_NODE";
									break;
								default:
									//contents="Undefined_Node";
									break;
								}
								return contents;
							},
							
							nodeType: function(elt){// retourne le type d'un �l�ment
								if (this.isString(elt))	elt = document.getElementById(elt); // si String cherche �l�ment objet
								var type;
								switch(elt.nodeType){
								case 1:
									type = "ELEMENT_NODE";
									break;
								case 2:
									type = "ATTRIBUTE_NODE";
									break;
								case 3:
									type="TEXT_NODE";
									break;
								case 4:
									type="CDATA_SECTION_NODE";
									break;
								case 5:
									type="ENTITY_REFERENCE_NODE";
									break;
								case 6:
									type="ENTITY_NODE";
									break;
								case 7:
									type="PROCESSING_INSTRUCTION_NODE";
									break;
								case 8:
									type="COMMENT_NODE";
									break;
								case 9:
									type="DOCUMENT_NODE";
									break;
								case 10:
									type="DOCUMENT_TYPE_NODE";
									break;
								case 11:
									type="DOCUMENT_FRAGMENT_NODE";
									break;
								case 12:
									type="NOTATION_NODE";
									break;
								default:
									type="Undefined_Node";
									break;
								}
								return type;
							},
							
							nodeChild: function(elt, binary){// retourne le nombre d'enfants d'un �l�ment HTML ou un Array() contenant les enfants 
								/*
								var n = cnx.dom().nodeChild(elt); //retourne le nombre d'enfants
								var tab = cnx.dom().nodeChild(elt, true); //retourne un Array() contenant la liste des enfants; utiliser split() pour le d�tail
								for (var i=0; i<tab.length; i++) {
									document.write("tableau[" + i + "] = " + tab[i] + "<BR>");
								}
								*/
								elt = cnx.dom().getElt(elt); // si String cherche �l�ment objet
								var tab = new Array();
								for (var i = 0; i < elt.childNodes.length; i++) {
									//elt.childNodes[i];
									tab[i] = elt.childNodes[i]; //penser � string.split(separateur)
								}
								if (binary) return tab; //penser � string.split(separateur)
								else	return i; //retourne le nombre d'enfants d'un �l�ment HTML; elt.childNodes.length ne retourne rien! Donc il faut i!!!
							},
								
							nodeAttributes: function(elt, binary){// retourne le nombre d'attributs ou un tableau avec les attributs
								/*
								var n = cnx.dom().nodeAttributes(elt); //retourne le nombre d'attributs
								var tab = cnx.dom().nodeAttributes(elt, true); //retourne un Array() contenant la liste des attributs; utiliser split() pour le d�tail
								for (var i=0; i<tab.length; i++) {
									document.write("tableau[" + i + "] = " + tab[i] + "<BR>");
								}
								*/
								elt = cnx.dom().getElt(elt);  // si String cherche �l�ment objet
								if (!elt.attributes) return 0;
								if (!binary)	return elt.attributes.length; //retourne le nombre d'attributs
								else {
									var tab = new Array();
									for (var i=0; i < elt.attributes.length; i++){
										tab[i] = elt.attributes[i].nodeName + "=>" +elt.attributes[i].nodeValue; //penser � string.split(separateur)
									}
									return tab;
								}
							},
							
							nodeParent: function(elt, niv){// renvoi l'�l�ment parent quelque soit son tag, juste le parent ou grand parent
								/*----------------------------------------------------
								Permet de r�cup�rer l'�l�ment parent
									- elt: �l�ment source (this) - nota peut �tre un id
									- niv: niveau du parent � r�cup�rer, optionnel permet de chercher un grand parent!
								exemple d'utilisation:
								var parent_table = searchParent(objetCellule); //retourne la row
								avec nodeName retourne le nom de l'�l�ment et "BODY" pour document.body
								---------------------------------------------------- */
								if (cnx.log().isString(elt))		elt = document.getElementById(elt); // si string cherche �l�ment objet
								(niv==undefined || niv<1) ? niv=1 : niv=niv;// On initialise le niveau � 1 si besoin est.
								if (elt.nodeName == "#document") return null; // "#document" est le premier ancestre de tous les objet HTML et n'a pas de parent
								if (niv != 1 && elt.parentNode){  // Si le nombre de niveaux demand� n'est pas atteint on continue
									return this.nodeParent(elt.parentNode, niv -= 1); 
								} else {
									return elt.parentNode; // retourne l'objet.
								}
							},
							
							searchTagParent: function(elt, tag, niv){// renvoi l'�l�ment parent correspondant � un Tag donn� 
								/*----------------------------------------------------
								Author: jsgorre Jean-s�bastien sur javascript codes sources
								Permet de r�cup�rer l'�l�ment parent correspondant � un Tag donn�
									- tag: Nom du type d'�l�ment � r�cup�rer: exemple TABLE
									- elt: �l�ment source (this) - nota peut �tre un id
									- niv: niveau du parent � r�cup�rer, optionnel
								exemple d'utilisation:
								var parent_table = searchParent(objetCellule, "TABLE"); //retourne la table parent
								---------------------------------------------------- */
								elt = cnx.dom().getElt(elt); // si string cherche �l�ment objet
								if(elt == false) return false; //gestion d'erreur
						
								(niv==undefined || niv<1) ? niv=1 : niv=niv;// On initialise le niveau � 1 si besoin est.
							
								if (elt.parentNode.nodeName == "#document")		return false;    // Le document a �t� parcouru enti�rement et aucune balise n'a �t� trouv�e        
								
								if (elt.parentNode.nodeName != tag){ // Si la balise ne correspond pas on continue la recherche                             
									return this.searchParent(elt.parentNode, tag, niv);	
								} else if (niv!=1 && elt.parentNode.parentNode.nodeName==tag){  // Si le nombre de niveaux demand� n'est pas atteint et qu'il reste des balises correspondantes on continue
									return this.searchParent(elt.parentNode, tag, niv-=1); 
								} else {
									return elt.parentNode; // Sinon on renvoie l'id de la balise correspondante
								}
							},
							
							firstChild: function (elt,tagName){ //retourne le premier tagName parmi la collection des tagName d'un elt, soit tagName[0] 
								if (this.isString(elt))		elt = document.getElementById(elt); // si string cherche �l�ment objet
								var elts = elt.getElementsByTagName(tagName);
								return elts && elts.length>0 ? elts[0] : null;
							}, 
							
							getElt: function (elt){ // retourne un objet m�me si id fournit 
								var object = cnx.log().isString(elt)	? document.getElementById(elt) : elt;
								if (cnx.log().isNull(object))	object = false;
								return object;
							}, 
							
							isElt: function (elt){	//elt est soit un objet soit un id: renvoie true si objet HTML; sinon false
								if (cnx.log().isString(elt))	elt = document.getElementById(elt);
								return !!(elt && elt.nodeType == 1); // issu de la classe Prototype: true si elt HTML autrement false
							}
						}; //end of return - dom -public section
				}), //end of dom() - la fonction anonyme n'est pas en auto ex�cution, elle admet des param�tres
			
				event: (function() { //fonction anonyme - gestion des �v�nements
						/* private section */
						var eventElt = (cnx.event.arguments[0]) ?  cnx.dom().getElt(arguments[0]) : false; //�l�ment sur lequel porte le style - var le rend inaccessible depuis l'ext�rieur de la classe
						return { //public section
								mouseWheel: function (e, fonction){ // Event handler for mouse wheel event - DOMMouseScroll{{{
									/** --------------------
									script trouv� sur:
									http://www.switchonthecode.com/tutorials/javascript-tutorial-the-scroll-wheel
									http://www.adomas.org/javascript-mouse-wheel/
									http://ajaxian.com/archives/javascript-and-mouse-wheels
									----------------------- */
									e = e ? e : window.event;
									var wheelData = e.detail ? e.detail * -1 : e.wheelDelta / 40; //mvt du scroll
									if (wheelData) eval("fonction(e, wheelData)"); //appel de la function associ�e: func(e, delta) - delta>0 scroll Up - delta<0 scroll down
									//return cnx.event().cancelEvent(e); //cancelEvent() inhibbe le scroll si besoin
									//return false; //ne pas utiliser return false car sous IE cela emp�che l'ex�cution du scroll associ� � mousewheel, donc m�me effet que cnx.event().cancelEvent()
								}, // }}}
								
								cancelEvent: function(e) { // arr�te l'ex�cution d'un event ex: scroll wheel {{{
									e = e ? e : window.event;
									if(e.stopPropagation)	e.stopPropagation();
									if(e.preventDefault)	e.preventDefault();
									e.cancelBubble = true;
									e.cancel = true;
									e.returnValue = false;
									return false;
								}, // }}}
								
								onEvent: function(eventName, func, elt){ // affecte un event avec la m�thode on...{{{
									/* -----------------
									normalement cette fonction est appel�e par cnx.event().addEvent()
									mais elle peut aussi �tre appel�e directement
									---------------------- */
									var elt = cnx.dom().getElt(elt); // si String cherche �l�ment objet
									eventName = eventName.toLowerCase(); //met en minuscule le nom de l'�v�nement
									if(eventName.indexOf("on") == 0) eventName = eventName.substring(2, eventName.length);//transforme onclick en click
									var oldEvent = elt["on" + eventName]; //m�morise les anciens �v�nements d�j� appliqu�s: elt.onmousedown
									if (typeof oldEvent != "function")	elt["on" + eventName] = func; //applique directement la function
									else {
										elt["on" + eventName] = function() {
											if (oldEvent)	oldEvent(); //applique les anciens event
											func(); //ajoute le nouvel event
										}
									}
								}, // }}}
								
								addEvent: function (eventName, func, elt) {//{{{
									/*-----------------------------------
									elt est soit un objet soit un id d'un objet (donc string id)
									eventName est de type string "load" ou "onLoad" pour onload
									func est le nom de la fonction - ne pas mettre les parenth�ses On �crira affiche et non pas affiche()
									
									sous Firefox mousedown n�cessite un traitement sp�cial pour �viter les conflits avec mousemove lors des drag and drop
									
									exemple: addEvent( "load", affiche, window);
									function affiche() { alert(1); }
									--------------------------------------*/
									eventElt = (elt) ?  cnx.dom().getElt(elt) : eventElt;
									eventName = eventName.toLowerCase(); //met en minuscule le nom de l'�v�nement
									if(eventName.indexOf("on") == 0) eventName = eventName.substring(2, eventName.length);//transforme onclick en click
									
									var propagation = false;
									
									switch(eventName) { //nom de l'event en minuscule sans le on
										case "mousedown":
											if (eventElt.attachEvent)	eventElt.attachEvent("on" + eventName, func); //Ne pas oublier le "on" pour IE
											else { //n'est pas IE
												cnx.event().onEvent("onmousedown", func, eventElt); //appelle l'event suivant la m�thode onmousedown
											}
											break;
										
										case "mousewheel": //onmousewheel - transmet une fonction sp�cifique haut/bas 
											cnx.event.funcEvent = func; //transmet le nom de la fonction � cnx.event().wheel()
											if(eventElt.addEventListener)  {
												eventElt.addEventListener('DOMMouseScroll', 
													function(){
														e=arguments[0] || event;
														cnx.event().mouseWheel(e, func);
													},
													false); //FF only - name event sp�cifique pour FF
												eventElt.addEventListener(eventName, 
													function(){
														e=arguments[0] || event;
														cnx.event().mouseWheel(e, func);
													},
													false);
											}
											else if(eventElt.attachEvent){
												if (eventElt == window)	eventElt = document; //IE ne supporte pas window, seulement document
												eventElt.attachEvent("on" + eventName, 
													function(){
														e=arguments[0] || event;
														cnx.event().mouseWheel(e, func);
													}
												); //IE
											}
											break;
										
										default:
											if (eventElt.attachEvent)	eventElt.attachEvent("on" + eventName, func); //Ne pas oublier le "on" pour IE
											else	eventElt.addEventListener(eventName, func, propagation);//mettre un 3i�me argument pour les autres navigateurs FF - optionnel au del� de la version 6 de FF}
											break;
									}
									return false;
								},//}}}
								
								removeEvent: function(eventName, func, elt){ // retire un event d'un objet {{{
									var elt = cnx.dom().getElt(elt); //existence de elt as object or as string - id
									if (eventName == "DOMMouseScroll")	eventName = "mousewheel"; //DOMMouseScroll est sp�cifique FF
									if(element.removeEventListener)	{
									if(eventName == 'mousewheel')	element.removeEventListener('DOMMouseScroll', func, false); // pour FF 
									element.removeEventListener(eventName, func, false);//chrome ou op�ra ou (FF si pas mousewheel)
									}
									else if(element.detachEvent)	element.detachEvent("on" + eventName, func); //pour IE
							
								}, // }}}
								
								getEvent: function(e){//retourne l'�v�nement{{{ 
									if (!e) e = window.event; //IE ne returne pas (e) pas offre une propri�t� window.event
									return e; //  e.type 	fourni le type de l'�v�nement: ex mousedown
								},//}}}
								
								getTarget: function(e){ //renvoie la cible d'un �v�nement{{{
									var cible;
									if (!e) var e = window.event; //IE ne returne pas (e) pas offre une propri�t� window.event
									if (e.target) cible = e.target;
									else if (e.srcElement) cible = e.srcElement;
									if (cible.nodeType == 3) 	cible = cible.parentNode; // defeat Safari bug
									return cible;
									/* ------------------------------------------
									cible.id //identificateur de l'objet si il existe
									cible.name //nom de l'objet ou undefined
									cible.tagName //type de l'objet input, body H1 p ...
									cible.object //confirme que sa nature est un objet, fourni l'objet lui-m�me cad cible en fait!
									--------------------------------------- */
								},// }}}
								
								getType: function(e){ //renvoi le type de l'Event {{{
									if (!e) e = window.event; //IE ne returne pas (e)
									return e.type;
								}, // }}}
								
								isleft: function(e){	//	{{{
									var isleftbutton = (window.event)? (window.event.button==1): (e.type=="mousedown")? (e.which==1): false;
									return isleftbutton; //ex si bouton.right=true alors bouton droit cliqu�
								},	//	}}}
								
								isright: function(e){	//	{{{
									var isrightbutton = (window.event)?(window.event.button==2): (e.which==3); //window.event pour browser clone IEX et e.which pour browser clone FF
									return isrightbutton; //ex si bouton.right=true alors bouton droit cliqu�
								},	//	}}}
								
								
								ismiddle: function(e){	//	{{{
									var ismiddlebutton = (window.event)? ((window.event.button==3) || (window.event.button==4)): (e.which==2);
									return ismiddlebutton; //ex si bouton.right=true alors bouton droit cliqu�
								},	//	}}}
								
								clientX: function(e){	//	{{{
									var clientX = (window.event)?(window.event.clientX): (e.clientX);// Position horizontale sur le client
									return clientX;
								},	//	}}}
								
								clientY: function(e){	//	{{{
									var clientY = (window.event)?(window.event.clientY): (e.clientY);// Position verticale sur le client
									return clientY;
								},	//	}}}
								
								screenX: function(e){	//	{{{
									var screenX = (window.event)?(window.event.screenX): (e.screenX);// Position horizontale � l'ecran du pointeur de la souris
									return screenX;
								},	//	}}}
								
								screenY: function(e){	//	{{{
									var screenY = (window.event)? (window.event.screenY): (e.screenY);// Position verticale � l'ecran du pointeur de la souris
									return screenY;
								},	//	}}}
								
								pageScrollX: function(e){	//pageX avec le scroll pour IE: X correspond � left	{{{
									var pageX = (window.event) ? (window.event.clientX + document.body.scrollLeft + document.documentElement.scrollLeft) : (e.pageX);// Position horizontale sur la page du pointeur de la souris
									return pageX; //position par rapport � left
								},	//	}}}
								
								pageScrollY: function(e){	//pageY avec le scroll pour IE: Y correspond � top	{{{
									var pageY = (window.event) ? (window.event.clientY + document.body.scrollTop + document.documentElement.scrollTop) : (e.pageY);// Position verticale sur la page du pointeur de la souris
									return pageY; //position par rapport � top
								},	//	}}}
							
								pageX: function(e){	//sous IE ne tient pas compte du scroll, utiliser pageScrollX pour coordonn�es avec le scroll	{{{
									var pageX = (window.event)?(window.event.clientX): (e.pageX);// Position horizontale sur la page du pointeur de la souris
									return pageX;
								},	//	}}}
								
								pageY: function(e){	//sous IE ne tient pas compte du scroll, utiliser pageScrollY pour coordonn�es avec le scroll	{{{
									var pageY = (window.event)?(window.event.clientY): (e.pageY);// Position verticale sur la page du pointeur de la souris
									return pageY;
								},	//	}}}
						
								ismousedown: function(e){	//	{{{
									var rep; //variable pour la r�ponse
									var nomEvent = cnx.event().getType(e); //nom ou type du dernier Event
									(nomEvent == "mousedown")? rep=true: rep=false; //vrai si Event = mousedown
									return rep;
								},	//	}}}
								
								ismouseup:  function(e){	//	{{{
									var rep; //variable pour la r�ponse
									var nomEvent = cnx.event().getType(e); //nom ou type du dernier Event
									(nomEvent == "mouseup")? rep=true: rep=false; //vrai si Event = mousedown
									return rep;
								},	//	}}}
								
								ismousemove: function(e){	//	{{{
									var rep; //variable pour la r�ponse
									var nomEvent = cnx.event().getType(e); //nom ou type du dernier Event
									(nomEvent == "mousemove")? rep=true: rep=false; //vrai si Event = mousedown
									return rep;
								},	//	}}}
							
								isclick: function(e){	//	{{{
									var rep; //variable pour la r�ponse
									var nomEvent = cnx.event().getType(e); //nom ou type du dernier Event
									(nomEvent == "click")? rep=true: rep=false; //vrai si Event = mousedown
									return rep;
								},	//	}}}
								
								isdblclick: function(e){	//	{{{
									var rep; //variable pour la r�ponse
									var nomEvent = cnx.event().getType(e); //nom ou type du dernier Event
									(nomEvent == "dblclick")? rep=true: rep=false; //vrai si Event = mousedown
									return rep;
								},	//	}}}
								
								iscontextmenu: function(e){	//	{{{
									var rep; //variable pour la r�ponse
									var nomEvent = cnx.event().getType(e); //nom ou type du dernier Event
									(nomEvent == "contextmenu")? rep=true: rep=false; //vrai si Event = mousedown
									return rep;
								},	//	}}}
								
								
								mousemove_afficheCoord: function(e){ //affiche les coord de la souris qui suivent le curseur de la souris	{{{
									if (!document.getElementById("cnxMouseCoordId" && cnx.event.postCoord == true && document.body)){ //  || ou &&
										var cnxMouseCoord = document.createElement("div");
										cnxMouseCoord.id = "cnxMouseCoordId";
										cnxMouseCoord.style.position = "absolute";
										cnxMouseCoord.style.visibility = "hidden";
										document.body.appendChild(cnxMouseCoord);
									}
									var cursor = document.getElementById("cnxMouseCoordId");
									if (cnx.event.postCoord == true){
										cnx.style(cursor).setVisibility("visible"); //cursor.style.visible = "visible";
										cursor.style.backGroundColor = "Transparent";
										cursor.innerHTML = "Left: "+cnx.event().pageScrollX(e) + "px"+ " Top: "+cnx.event().pageScrollY(e) + "px"; //Left
										cursor.style.top = cnx.event().pageScrollY(e)  + 1 + "px"; //d�calage pour even mouseover et lecture
										cursor.style.left = cnx.event().pageScrollX(e) + 1 + "px";
									} 
									else cnx.style(cursor).setVisibility("hidden"); //cursor.style.visible = "hidden";
							
									return false;
								},
								
								postCoord: false //cnx.event.postCoord = true; pour afficher les coordonn�es de la souris - ; ne sert � rien ici, m�morisation du process!
						}; //end of return - event
				}), //end of event() - la fonction anonyme n'est pas en auto ex�cution, elle admet des param�tres
				
				style: (function() { //fonction anonyme - gestion des styles
						//private section
						var styleElt = (cnx.style.arguments[0]) ?  cnx.dom().getElt(arguments[0]) : false; //�l�ment sur lequel porte le style - var le rend inaccessible depuis l'ext�rieur de la classe
						//end of private section
						return { //public section
							
							appendStyle: function (styles) {// permet ajouter un style CSS via un fichier js, le CSS est inclus dans le js{{{
								/* -------------------------------------------
								Appending Style Nodes with Javascript by Jon Raasch
								
								Permet d'ajouter des styles directement dans un js
								Il faut d�finir les styles comme ceci:
								
								var styles = '#header { color: red; font-size: 40px; font-family: Verdana, sans; }';
								styles += ' .content { color: blue; text-align: left; }';
								---------------------------------------- */
								var css = document.createElement('style');
								css.type = 'text/css';
								
								if (css.styleSheet) css.styleSheet.cssText = styles;
								else css.appendChild(document.createTextNode(styles));
								
								document.getElementsByTagName("head")[0].appendChild(css); //ajoute le style
							},//}}}
						
							isClassName: function (sClassName, elt){//search className{{{
								/*
								Cherche tous les syles de type className appliqu� � un objet elt
								puis recherche si le style est trouv� dans l'ensemble de ces styles
								*/
								var recherche = false;
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; // si String cherche �l�ment objet
								if(styleElt == false)	return false;
								var liste_className = styleElt.className;//retourne tous les styles de type className en une seule liste s�par�e par un espace
								tab_className = liste_className.split(" ");//transforme la liste en un tableau contenant chacun des className appliqu�s � styleElt
								for(var i = 0 ; i < tab_className.length ; i++){ //parcours le tableau pour voir si l'objet est un contener
									if(tab_className[i] == sClassName){
										recherche = true;
									}
								}
								return recherche;
							}, //}}}
							
							addClassName: function(sClassName, elt) { //ajoute un className{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; // si String cherche �l�ment objet
								var s = styleElt.className;
								var p = s.split(" ");
								var l = p.length;
								for (var i = 0; i < l; i++) {
									if (p[i] == sClassName)
										return;
								}
								p[p.length] = sClassName;
								styleElt.className = p.join(" ").replace( /(^\s+)|(\s+$)/g, "" );
								return true;
							}, //}}}
						
							removeClassName: function(sClassName, elt) {//retire un className{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; // si String cherche �l�ment objet
								var s = styleElt.className;
								var p = s.split(" ");
								var np = [];
								var l = p.length;
								var j = 0;
								for (var i = 0; i < l; i++) {
									if (p[i] != sClassName)
										np[j++] = p[i];
								}
								styleElt.className = np.join(" ").replace( /(^\s+)|(\s+$)/g, "" );
								return true;
							}, //}}}
							
							unit: "", //fourni l'unit� de mesure: exemple: "px"
						
							getStyle: function(str_style, elt) { //lit la valeur du style {{{
								/* -----------------------------------
								getstyle() renvoie la valeur du style
								id_element est l'identificateur de l'�l�ment (div, img ...), donc String, mais g�re aussi les object
								style est le nom du style dont la valeur sera retourn�e: width, height, top, left ...
								en fonction de la propri�t� test�e getstyle retourne une String ou un Interger, voire #FFF ou rgb() ...
								------------------------- */
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var str_value = (styleElt).style[cnx.style().toJavascriptStyleName(str_style)]; //lecture des styles int�gr� au code HTML
								if(!str_value){ //lecture de style dans un fichier CSS ou �quivallent
									if(document.defaultView)	str_value = document.defaultView.getComputedStyle(styleElt, null).getPropertyValue(str_style); //FF et Opera
									else if((styleElt).currentStyle)	str_value = (styleElt).currentStyle[cnx.style().toJavascriptStyleName(str_style)]; //IEX
								}
								return str_value; //String: => width: "100px",  faire:  parseInt(str_value) pour integer
							}, // }}}
							
								
							
							setStyle: function(str_style, str_value, elt) {	// applique un style {{{
								/* ------------------------------
								setstyle() sert � d�finir, � appliquer une valeur � une style
								(elt) est l'identificateur de l'�l�ment: div, img, donc String, mais g�re aussi les object
								str_style est le nom du style � modifier: width, top, ... au format html avec tiret et String
								str_value est la nouvelle valeur du style � appliquer � id_element
								----------------------------- */
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								//alert("classe style: " + styleElt.id);
								var op_correct = false;
								if (styleElt)	op_correct = (styleElt).style[cnx.style().toJavascriptStyleName(str_style)] = str_value; //retourne str_value si op�ration correctement effectu�e
								return op_correct;
							},	// }}}
							
							
							getUnit: function(str_value){ // retourne l'unit� utilis�e; exemple: "px"  {{{
								var modele = /[0-9]/g; //recherche tous les nombres
								cnx.style.unit = str_value.replace(modele, ""); //retourne la partie texte, donc l'unit� utilis�e
								return cnx.style.unit; //String
							},	// }}}
							
							getWidth: function(elt){	// {{{
						
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var str_value = cnx.style().getStyle("width", styleElt);
								if (str_value == "auto"){ //gestion pour IE qui retourne auto si la table s'ajsute automatiquement � la fenetre
									var largeur = styleElt.offsetWidth;
									cnx.style.unit = "px";
								}
								else {
									var largeur =  parseInt(str_value); 
									cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								}
								return parseInt(largeur); // c'est un integer
							},	// }}}
							
							setWidth: function(str_value, elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								str_value = (cnx.log().isString(str_value)) ? str_value : str_value + "px"; //v�rifie que c'est un String
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								cnx.style().setStyle("width", str_value, styleElt); //applique le style
								return parseInt(str_value); //retourne un integer
							},	//	}}}
							
							getTruePosition: function(elt){ // retourne la position d'un elt par rapport � la page (y compris avec ascenseur et parent en position absolue) {{{
								/*----------
								script trouv� sur: http://forum.hardware.fr/hfr/Programmation/HTML-CSS-Javascript/javascript-connaitre-position-sujet_45951_1.htm
								code de Herm�s le messager sur ce forum
								
								<img src="../images/back.gif" width="116" height="16" id="smile01" class="dragRelative" >
								var pos = cnx.style().getpos("smile01");
								pos.x contient la position par rapport au bord gauche de la page web, soit un offsetLeft global
								pos.y contient la position par rapport au bord haut de la page web, soit un offsetTop global
								-------- */
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; //g�re id ou objet HTML
								var objet = new Object(); //gen�re un objet; si objet = elt on provoque une erreur avec FF version 3, mais avec les nouvelles versions de FF ni IE
								var x = 0;
								var y = 0;
								while (styleElt.tagName != 'BODY'){ //tant que BODY n'est pas le parent
									x += styleElt.offsetLeft;
									y += styleElt.offsetTop;
									styleElt = styleElt.offsetParent;
								}
								objet.x = x; //offsetLeft global � la page web
								objet.y = y; //offsetTop global � la page web
								//alert("getPos: "+x+" : "+y);
								return objet; //contient l'objet HTML initial avec 2 propri�t�s x=left; y=top par rapport � la page web m�me si ascenseur
							}, // }}}
							 
							getTrueLeft: function(elt){ // position left par rapport � la page y compris si ascenseur et parent en position absolue {{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; //g�re id ou objet HTML
								styleElt = cnx.style().getTruePosition(styleElt); //retourne x, y postion de elt par rapport � la page y compris si ascenseur et parent en position absolue
								return styleElt.x; // x => left: as integer
							}, // }}}
							
							getTrueTop: function(elt){ // position top par rapport � la page y compris si ascenseur et parent en position absolue {{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; //g�re id ou objet HTML
								styleElt = cnx.style().getTruePosition(styleElt); //retourne x, y postion de elt par rapport � la page y compris si ascenseur et parent en position absolue
								return styleElt.y; // y => top: as integer
							}, // }}}
							
							getTrueHeight: function(elt) { //taille r�elle d'une image ici height{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; //g�re id ou objet HTML
								var image = cnx.dom().getElt(styleElt); //r�cup�re l'image soit par id soit par objet
								var newImg = new Image();// Declaration d'un objet Image
								newImg.src = image.src;// Affectation du chemin de l'image a l'objet
								var h = newImg.height;// On recupere les tailles reelles
								var w = newImg.width;// On recupere les tailles reelles
								newImg = null; //d�truit image
								return h; //as integer
							}, // }}}
							
							getTrueWidth: function(elt) { //taille r�elle d'une image ici width{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; //g�re id ou objet HTML
								var image = cnx.dom().getElt(styleElt); //r�cup�re l'image soit par id soit par objet
								var newImg = new Image();// Declaration d'un objet Image
								newImg.src = image.src;// Affectation du chemin de l'image a l'objet
								var h = newImg.height;// On recupere les tailles reelles
								var w = newImg.width;// On recupere les tailles reelles
								newImg = null; //d�truit image
								return w; //as integer
							}, // }}}
						
							
							setTop: function(str_value, elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								str_value = (cnx.log().isString(str_value)) ? str_value : str_value + "px"; //v�rifie que c'est un String
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								cnx.style().setStyle("top", str_value, styleElt); //applique le style
								return parseInt(str_value); //retourne un integer
							},	//	}}}
							
							getTop: function(elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var str_value = cnx.style().getStyle("top", styleElt);
								if (str_value == "auto")	str_value = styleElt.offsetTop + "px";
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								return parseInt(str_value); //integer
							}, 	//	}}}
							
							setLeft: function(str_value, elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								str_value = (cnx.log().isString(str_value)) ? str_value : str_value + "px"; //v�rifie que c'est un String
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								cnx.style().setStyle("left", str_value, styleElt); //applique le style
								return parseInt(str_value); //retourne un integer
							},	//	}}}
							
							getLeft: function(elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var str_value = cnx.style().getStyle("left", styleElt);
								if (str_value == "auto")	str_value = styleElt.offsetLeft + "px";
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								return parseInt(str_value); //integer
							}, 	//	}}}
							
							setPosition: function(strPosition, elt){ //	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								cnx.style().setStyle("position", strPosition, styleElt); 
								return strPosition;
							},	//	}}}
							
							getPosition: function(elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var strPosition = cnx.style().getStyle("position", styleElt); 
								return strPosition;
							},	//	}}}
							
							getRight: function(elt){ //	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var str_value = cnx.style().getStyle("right", styleElt);
								if (str_value == "auto")	str_value = styleElt.offsetRight + "px";
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								return parseInt(str_value); //integer
							}, //	}}}
							
							setRight: function(str_value, elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								str_value = (cnx.log().isString(str_value)) ? str_value : str_value + "px"; //v�rifie que c'est un String
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								cnx.style().setStyle("right", str_value, styleElt); //applique le style
								return parseInt(str_value); //retourne un integer
							}, // }}}
							
							getHeight: function(elt){ //	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var str_value = cnx.style().getStyle("height", styleElt);
								if (str_value == "auto")	str_value = styleElt.offsetHeight + "px";
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								return parseInt(str_value); //integer
							}, //	}}}
							
							setHeight: function(str_value, elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								str_value = (cnx.log().isString(str_value)) ? str_value : str_value + "px"; //v�rifie que c'est un String
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								cnx.style().setStyle("height", str_value, styleElt); //applique le style
								return parseInt(str_value); //retourne un integer
							}, // }}}
							
							
							setBottom: function(str_value, elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								str_value = (cnx.log().isString(str_value)) ? str_value : str_value + "px"; //v�rifie que c'est un String
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								cnx.style().setStyle("bottom", str_value, styleElt); //applique le style
								return parseInt(str_value); //retourne un integer
							},	//	}}}
							
							getBottom: function(elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var str_value = cnx.style().getStyle("bottom", styleElt);
								if (str_value == "auto")	str_value = styleElt.offsetBottom + "px";
								cnx.style.unit = cnx.style().getUnit(str_value); //unit� utilis�e: cnx.style.unit
								return parseInt(str_value); //integer
							}, 	//	}}}
							
							setVisibility: function(strVisibility, elt){ //	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								if (strVisibility == true) strVisibility = "visible";
								if (strVisibility == false) strVisibility = "hidden";
								cnx.style().setStyle("visibility", strVisibility, styleElt); 
								return strVisibility;
							},	//	}}}
							
							getVisibility: function(elt){	//	{{{
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var strVisibility = cnx.style().getStyle("visibility", styleElt); 
								return strVisibility;
							},	//	}}}
							
							setMultipleStyle: function(str_style, elt){ // {{{
								/* ----------------------------
								Re�oit une chaine de caract�res de type : position:absolute; left: 10px; top: 20px;
								Applique alors chacun de ces styles
								--------------------- */
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt;
								var table_array = cnx.style().styleExtraction(str_style); //retourne la liste des styles et leur valeur d�compos�e en un seul array
								for (var i=0; i<table_array.length; i = i+2) { //parcours le tableau contenant le nom et la valeur des styles � appliquer
									cnx.style().setStyle(table_array[i], table_array[i+1], styleElt); //i est le nom du style, i+1 sa valeur � appliquer
								}
							}, // }}}
						
							styleExtraction: function(chaine){ // {{{
								/* -----------------------------------------
								En HTML il est possible de d�finir un style comme suit:
								<img src="image.gif" style="position: absolute; border: 1px;" />
								Nous avons souhait� reproduire dans la classe style cette possibilit�
								Ecrire sur une seule ligne plusieurs instructions de style
								Tout en gardant �galement un format similaire au HTML
								Il nous fallait alors pouvoir d�composer cette ligne en instruction pour chacun des styles employ�s
								Tel est le r�le de styleExtraction()
								------------------------------------------- */
								chaine = trim(chaine); //supprime les espaces en d�but et fin de chaine
								var reg=new RegExp("[ :;]+", "g"); //expression r�guli�re, recherche dans toute la chaineles caract�res : et ; en �liminant les espaces interne
								var tableau = chaine.split(reg); //transforme la chaine de caract�res en tableau en fonction des crit�res de recherche de l'expression r�guli�re
								var fin = tableau.length -1; //cherche l'indice du dernier �l�ment du tableau
								if (tableau[fin].length == 0) tableau.pop(); //supprime le dernier �l�ment si son contenu est null
								return tableau; //retourne un tableau � partir de la chaine de caract�res pass�e en param�tre
							}, // }}}
							
							toJavascriptStyleName: function(text){ // {{{
								/* ----------------------------------------
								En HTML le nom de certains styles s'�crive avec un tiret comme: background-color
								Ce m�me style en javascript s'�crit	en supprimant le tiret: backgroundColor
								toJavascriptStyleName() permet de transformer un style compos� avec tiret en un style format javascript
								sur les autres nom de style, rien ne se produit
								---------------------------- */
								var modele= /-/;
								while(modele.test(text)){
									var pos=text.search(modele);
									text=text.substring(0, pos) + text.charAt(pos+1).toUpperCase() + text.substring(pos+2, text.length);
								}
								return text;
							}, // }}}
							
							setOpacity: function(opacity, elt) { // Opacit� {{{
								/* ---------------------
								script trouv� sur: http://www.supportduweb.com/scripts_tutoriaux-code-source-32-changer-l-opacite-d-un-div-alpha-compatibles-avec-tous-les-navigateurs.html
								opacity as integer between 0 /100
								100 => opacit� = 100% le texte est normal
								0 => opacit� = 0% le texte est totalement transparent, donc un texte en noir sur fond blanc avec opacity=0 dispara�t! => totalement transparent
								------------------------- */
								styleElt = (elt) ?  cnx.dom().getElt(elt) : styleElt; //re�oit id ou object HTML, retourne Object HTML
								if (!styleElt) return false;
								//var color = cnx.style().getStyle("background-color", styleElt);
						
								styleElt.style["filter"] = "alpha(opacity="+opacity+")";
								styleElt.style["-moz-opacity"] = opacity/100;
								styleElt.style["-khtml-opacity"] = opacity/100;
								styleElt.style["opacity"] = opacity/100;
								return true;
							} // }}}
								
								
						}; //end of return - public section - style()
				}), //end of style() - la fonction anonyme n'est pas en auto ex�cution, elle admet des param�tres
			
				log: (function() { // logique, reg expression, is quelquechose - fonction anonume
					/* private section */
					return { //public section
						trim: function (aString) { // Supprime les espaces inutiles en d�but et fin de la cha�ne pass�e en param�tre.{{{
							/* ---------------------------------------------------
							Retourne la cha�ne sans ses espaces
							Trouver sur: http://anothergeekwebsite.com/fr/2007/03/trim-en-javascript
							Trim en Javascript
							Posted 20. March 2007 - 10:28 by papy.reno
							----------------------------------------------------- */
							if (aString.trim())		return aString.trim(); //new browser
							var regExpBeginning = /^\s+/;
							var regExpEnd = /\s+$/;
							return aString.replace(regExpBeginning, "").replace(regExpEnd, "");
						},//}}}
						
						ltrim: function (aString) { // Supprime les espaces inutiles en d�but de la cha�ne pass�e en param�tre{{{
							/* ---------------------------------------------------
							Retourne la cha�ne sans ses espaces
							Trouver sur: http://anothergeekwebsite.com/fr/2007/03/trim-en-javascript
							Trim en Javascript
							Posted 20. March 2007 - 10:28 by papy.reno
							----------------------------------------------------- */
							if (aString.trimLeft())		return aString.trimLeft(); //new browser
							var regExpBeginning = /^\s+/;
							return aString.replace(regExpBeginning, "");
							},//}}}
					
					
						rtrim:function (aString) { // Supprime les espaces inutiles en fin de la cha�ne pass�e en param�tre.{{{
							/* ---------------------------------------------------
							Retourne la cha�ne sans ses espaces
							Trouver sur: http://anothergeekwebsite.com/fr/2007/03/trim-en-javascript
							Trim en Javascript
							Posted 20. March 2007 - 10:28 by papy.reno
							----------------------------------------------------- */
							if (aString.trimRight())	return aString.trimRight(); //new browser
							var regExpEnd = /\s+$/;
							return aString.replace(regExpEnd, "");
						},	//	}}}
						
						leftSubstring: function(chaine, strSearch){ //recherche la racine d'un �l�ment; partie gauche d'une chaine de caract�re; �quivallent � search_racine {{{
							if(cnx.log().isObject(chaine)) chaine = chaine.id; //transforme un objet en id en cas de besoin
							var leftRacine = chaine.substring(0, chaine.indexOf(strSearch)); //retourne la partie � gauche de chaine par rapport � strSearch
							return leftRacine;
						},	//	}}}
					
						d2b: function (int_d) {return int_d.toString(2);}, //transforme un nombre d�cimal en une chaine binaire
						b2d: function (str_h) {return parseInt(str_h,2);}, //transforme une chaine binaire en un entierd�cimal
						d2o: function (int_d) {return int_d.toString(8);}, //transforme un nombre d�cimal en une chaine octal
						o2d: function (str_h) {return parseInt(str_h,8);}, //transforme une chaine octal en un entier d�cimal
						d2h: function (int_d) {return int_d.toString(16);}, //transforme un nombre d�cimal en une chaine hexad�cimale
						h2d: function (str_h) {return parseInt(str_h,16);}, //transforme une chaine hexad�cimale en un entier d�cimal
						chr: function (int_ascii) {return String.fromCharCode(int_ascii);}, //retourne le caract�re correspondant au code ASCII fournit en argument (type d�cimal)
						asc: function (str_chaine, int_pos) {return str_chaine.charCodeAt(int_pos);}, //retourne le caract�re ASCII situ� � int_pos dans la chaine de caract�re str_chaine
					
						RGBtoHex: function(int_R,int_G,int_B) { //Conversion Couleur: fournie en RGB en un code hexa{{{
							return cnx.log().toHex(int_R)+cnx.log().toHex(int_G)+cnx.log().toHex(int_B); //return a string, penser � ajouter "#" pour afficher une couleur
							},//}}}
					
						toHex: function(N) {//{{{
							if (N==null) return "00";
							N=parseInt(N);
							if (N==0 || isNaN(N)) return "00";
							N=Math.max(0,N);
							N=Math.min(N,255);
							N=Math.round(N);
							return "0123456789ABCDEF".charAt((N-N%16)/16) + "0123456789ABCDEF".charAt(N%16);
						},//}}}
					
						HextoRGB: function(str_Hex){ //Conversion Couleur: attention il faut le # dans str_Hex; Converti une couleur fournie en hexa en un code RGB{{{
							var colorRGB = new Object();
							colorRGB.R = this.HexToR(str_Hex);
							colorRGB.G = this.HexToG(str_Hex);
							colorRGB.B = this.HexToB(str_Hex);
							return colorRGB; //il faut r�cup�rer chacune des composantes R G B de l'objet colorRGB
						}, //}}}
						
						HexToR: function(h) {	//Conversion Couleur	{{{
							return parseInt((this.cutHex(h)).substring(0,2),16);
						},	//	}}}
						HexToG: function(h) {	//Conversion Couleur	{{{
							return parseInt((this.cutHex(h)).substring(2,4),16);
						},	//	}}}
						HexToB: function(h) {	//Conversion Couleur	{{{
							return parseInt((this.cutHex(h)).substring(4,6),16);
						},	//	}}}
							
						cutHex: function(h) {	//Conversion Couleur	{{{
							return (h.charAt(0)=="#") ? h.substring(1,7):h;
						},	//	}}}
						
						isNotNull: function(elt){ //{{{
							(elt == null)?  retour = false:  retour = true;
							return retour; //renvoie true si la donn�e n'est pas null
						}, //}}}
					
						isNull: function(elt){ //{{{
							(elt == null)?  retour = true:  retour = false;
							return retour; //renvoie true si le don�es est null
						}, //}}}
					
						isNumber: function(elt){	//	{{{
							return typeof elt === "number";
						},	//	}}}
					
						isString: function(elt){	//	{{{
							return typeof elt === "string";
						},	//	}}}
					
						isUndefined: function(elt) {	//	{{{
							return typeof elt === "undefined"; //retourne true si undefined
						},	//	}}}
						
						isNotUndefined: function(elt) {	//	{{{
							return !cnx.log().isUndefined(elt); //revoie true si la variable est d�finie, autrement false
						},	//	}}}
							
					
						isArray: function(elt) {	//	{{{
							/* ---------------------------------------
							Array et Object avec typeof retourne "object";
							Array poss�de une propri�t� length qui peut �tre 0 si aucun �l�ment dans le tableau;
							Object n'a pas de propri�t� length et Object.length => undefined
							-------------------------------------------- */
							return typeof elt === "object" && (elt.length > -1); 
						},	//	}}}
					
						isObject: function(elt) {	//	{{{
							/* -------------------------------------------------
							Object et Array avec typeof retourne "object";
							Object n'a pas de propri�t� length et Object.length => undefined;
							Array a toujours une propri�t� length qui peut �tre �gale � 0 en l'absence d'�l�ment dans le tableau
							------------------------------------------ */
							return	typeof elt === "object" && typeof elt.length === "undefined";
						},	//	}}}
					
						isTable: function(elt){	//	{{{
							/* --------------------------
							on cherche � tester un objet <table>
							<table> est un objet avec une collection rows
							-------------------------------- */
							return this.isObject(elt) && this.isNotNull(elt.rows);
						},	//	}}}
					
						isFunction: function(elt) {	//	{{{
							/* ------------------------------------------
							une classe JSON: var a={} retourne "object" et non pas "function" avec typeof;
							une classe closure retourne "function"
							les "function" ont une propri�t� length qui semble toujours = 0!
							----------------------------------------- */
							return typeof elt === "function"; 
						},	//	}}}
					
						isWhat: function(elt){ //return un "string" donnant le type de l'�l�ment {{{
							if (this.isNull(elt)) return "null";
							else {
								if (this.isNumber(elt)) return "number";
								if (this.isString(elt)) return "string";
								if (this.isUndefined(elt)) return "undefined";
								if (this.isArray(elt)) return "array";
								if (this.isObject(elt)) return "object";
								if (this.isFunction(elt)) return "function";
							}		
						},	//	}}}
						
						isDefined: function(variableAsString, defaultValue) {	//	{{{
							/* ------------------------------------------------------------------
							variableAsString:  c'est � dire si data est le nom de la variable, re�oit "data"
							defaultValue: valeur par d�faut � appliquer si la variable n'existe pas
							si defaultValue est ommis il aura la valeur false
							
							Permet de tester la d�claration d'une variation.
							"is not Defined"  est diff�rend de undefined
							"is not defined" signifie que la variable n'existe pas, n'est pas d�clar�e!
							Cela entraine donc une erreur d'o� la gestion d'erreur associ�e � ce programme.
							
							Par d�faut cr�er la variable si elle nexiste pas en lui affectant defaultValue qui vaut false en absence d'autre valeur
							cnx.log().isDefined("variable"); ou	 cnx.log().isDefined("variable", 2);
							----------------------------------------------- */
							if (!defaultValue) 	defaultValue = false;//teste l'existence de la variable defaultValue et lui affecte par d�faut la valeur: false
							var existe = true; //nous supposons que la variable existe, est d�finie!
							try {
								eval(variableAsString); //evalue, calcule la variable
							} 
							catch(error) {
								existe = false; //il y a une erreur, donc la variable n'est pas d�finie
								//alert("catch: "+error); 
							}
							finally {
								if(!existe)	{eval(variableAsString+"='"+defaultValue+"';")}; //donne une valeur par defaut � la variable test�e si elle n'existe pas
								return existe;
							}
						},	//	}}}
						
						isNotDefined: function(variableAsString, valeur) {	//	{{{
							/* ------------------------------------------------------------------
							variableAsString:  c'est � dire si data est le nom de la variable, re�oit "data"
							valeur: valeur par d�faut � appliquer si la variable n'existe pas
							si valeur est ommis il aura la valeur false
							
							Permet de tester la d�claration d'une variation.
							"is not Defined"  est diff�rend de undefined
							"is not defined" signifie que la variable n'existe pas, n'est pas d�clar�e!
							Cela entraine donc une erreur d'o� la gestion d'erreur associ�e � ce programme.
							
							Par d�faut cr�e la variable si elle nexiste pas en lui affectant valeur qui vaut false en absence d'autre valeur
							if (cnx.log().isNotDefined("essai")) { //est true si essai n'existe pas, autrement est false
							essai = cnx.log().isNotDefined("essai"); 	//si essai n'existe pas, g�n�re une variable essai qui contient true, si essai existe d�j� elle conserve sa valeur intiale  
							essai = cnx.log().isNotDefined("essai", 2); //si essai n'existe pas, g�n�re une variable essai qui contiendra 2, autrement essai conserve sa valeur initiale
							----------------------------------------------- */
							var erreur = false; //nous supposons qu'il n'y a pas d'erreur donc que la variable existe, est d�finie!
							try {
								eval(variableAsString); //evalue, calcule la variable
							} 
							catch(error) {
								erreur = true; //il y a une erreur, donc la variable n'est pas d�finie
								//alert("catch: "+error); 
							}
							finally {
								if(erreur)	{ //une erreur existe, donc la variable n'est pas d�finie
									if (valeur || valeur == 0 || valeur == false){ //valeur existe, je veux cr�er la variable
										/*
										var texte = variableAsString+'="'+valeur+'";';
										eval(texte); //g�n�re la variable; en fait pas utile
										*/
										return valeur;
									}
									else{ //valeur n'existe pas, je ne veux pas cr�er la variable
										return erreur;
									}
								}
								else { //la variable existe
									return eval(variableAsString); //je retourne la valeur de la variable qui existe
								}
							}
						},	// retourne true ou false: true si erreur, donc variable non d�finie initialement et mise � false par d�faut}}}
						
						isHash: function(object) { // fonction issu de la classe Prototype {{{
							return object instanceof Hash;
						},	//	}}}
				
						generatePassword: function(plength){ //	{{{
							//Un generateur de mot de passe - par lecodejava.com
							if (this.isNull(plength)) var plength=16; //alloue une longueur par d�faut
							var keylist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789";
							var password=""; //initialise le password
							for (var i=0; i<plength; i++)
								password += keylist.charAt(Math.floor(Math.random()*keylist.length)); //calcule le mot de passe rendu al�atoire pat Math.random, Math.floor retourne un entier
							return password;
						},	//	}}}
						
						aleatoire: function(nombreTirages, nombreMax, nombreMini){
							/* --------------------------
							PLF- http://www.jejavascript.net/
							Ce script effectue un tirage o� chaque num�ro ne peut �tre tir� qu'une seule fois.
							On tire nombreTirages nombre compris entre nombreMini et nombreMax
							si nombreMini est ommis, alors nombreMini vaut 1
							----------------------------- */
							var contenuTirage = new Array;
							var nombre;
							if (!nombreMini)	nombreMini = 1; //gestion d'erreur
							var nombreMaxTirages = nombreMax - nombreMini +1;
							if (nombreTirages > nombreMaxTirages)		nombreTirages = nombreMaxTirages; //gestion erreur
							for (i=0; i < nombreTirages ;i++){
								nombre = Math.floor(Math.random() * nombreMax)+1; //retourne un nombre au hasard entre 1 et nombreMax
								if (nombre >= nombreMini){
									contenuTirage[i]= nombre;
									for (t=0 ; t < i ;t++){
										if (contenuTirage[t]==nombre){ //si nombre existe d�j� refait un tirage en d�cr�mentant i
											i--;
										}
									}
								}
								else i--;
							}
							if (nombreTirages == 1){
								var retour = contenuTirage[0];
								return retour;
							}
							return contenuTirage;
						}
					}; //end of return
				}), //end of log - cnx.log().trim()
				
				user: (function() { //fonction anonyme// browser navigateur
						/* private section */
						return { //public section
							IE: navigator.userAgent.indexOf('MSIE') > -1,
							FF: navigator.userAgent.indexOf('Firefox') > -1,
							Opera:  Object.prototype.toString.call(window.opera) == '[object Opera]',
							WebKit:         navigator.userAgent.indexOf('AppleWebKit/') > -1,
							Gecko:          navigator.userAgent.indexOf('Gecko') > -1 && navigator.userAgent.indexOf('KHTML') === -1,
							Chrome:			navigator.userAgent.indexOf('Chrome') > -1,
							MobileSafari:   /Apple.*Mobile/.test(navigator.userAgent)
						}; //end of return - public section
				}), //la fonction anonyme n'est pas en auto ex�cution - cnx.user().IE
				
				divers: (function() { //fonction anonyme 
						/* --------------------
						la fonction n'est pas en auto ex�cution
						elle peut donc recevoir des param�tres lors de son appel
						cnx.divers("moi").getParam(); //retourne "moi"
						------------------- */
						//private section - start
						var parametre = arguments[0] || false;
						//private section - end
						return { //public section -start
							author: "cnxclaude2",
							getParam: function(){
								return parametre; //retourne divers.arguments[0] si il existe un argument!
							},
							setAuthor: function(texte){
								cnx.divers().author = texte;
								return texte;
							}
							
						}; //public section -end
				}), //la fonction anonyme n'est pas en auto ex�cution
				
				
				generator: "jEdit" //ne pas mettre de virgule ou point virgule
			}; //fin public section - return
	
	})(); //end of cnx - noter les () donc auto executable, pas de param�tre
	
	cnx.event().addEvent( "mousemove", cnx.event().mousemove_afficheCoord, document, false); //document.onmousemove = drag_mousemove;
})(); //end of anonyme fonction 
