/* ----------------------------
Permet de faire un effet zoom ou loupe sur une image
l'image � zoomer est identifi�e par <img class="cnxzoom" ...
voir notamment:
http://www.laredoute.fr/vente-jupe-et-string-ficelle.aspx?productid=324196784&documentid=999999&categoryid=44596656&cod=4132fr4311144847141

Copyright et r�gles d'utilisation:
L'utilisation de ce code ou tout code d�riv� est soumis � notre accord
Merci de laisser ces lignes
Merci de nous faire parvenir toutes les �volutions de code que vous pouvez apporter � ce logiciel
Pour nous contacter:
claudecnx@blanquefort.net

Pour ins�rer ce fichier: Penser � actualiser le chemin selon votre besoin
<script src="http://jpconnexion.free.fr/jpclibrary_script/cnx.json.js"></script>
<script src="http://jpconnexion.free.fr/jpclibrary_script/zoom.json.js"></script>
en localhost faire
<script src="../jpclibrary_script/cnx.json.js"></script>
<script src="../jpclibrary_script/zoom.json.js"></script> 
---------------------------- */
(function(){ //fonction anonyme conteneur pour cnx.zoom
	
cnx.zoom = (function(){ //conteneur classe
	/** private section */


	return { // public section
		version: "Zoom loupe JSON version 2011-12-22",
		iszoom: false, //contient l'image cible dont nous devons faire un effet zoom
		ratio: false, //ratio entre taille actuelle et taille r�elle de l'image
		actualWidth: false, //largeur actuelle de l'image cible
		actualHeight: false, //hauteur actuelle de l'image cible
		realLeft: false, //postion r�elle de l'image cible par rapport � la page web
		realTop: false, //postion r�elle de l'image cible par rapport � la page web
	
		mouseover: function(e){ // identifie image et cr�e la copie {{{
			if (cnx.zoom.iszoom)	return false; //les div existe d�j�
			var cible = cnx.event().getTarget(e);
			if (cnx.style().isClassName("cnxzoom", cible)){ //l'image doit effectivement avoir un effet zoom -teste le style class cnxzoom
				//cnx.surv("In: " + cible.id);
				cnx.zoom.iszoom = cible; //m�morise l'image cible
				
				/* recherche des dimensions et position de l'image cible */
				var realWidth = cnx.style().getTrueWidth(cible); //taille r�elle de l'image
				var realHeight = cnx.style().getTrueHeight(cible); //taille r�elle de l'image
				cnx.zoom.actualWidth = cnx.style().getWidth(cible); //taille actuelle de l'image
				cnx.zoom.actualHeight = cnx.style().getHeight(cible); //taille actuelle de l'image
				cnx.zoom.ratio = realWidth / cnx.zoom.actualWidth; //ratio entre taille r�elle et taille actuelle de l'image � zoomer
				cnx.zoom.realLeft = cnx.style().getTrueLeft(cible); //position r�elle de l'image
				cnx.zoom.realTop = cnx.style().getTrueTop(cible); //position r�elle de l'image
				var decalage = 20; //d�callage entre image actuelle et sa copie pour le zoom
				//if (cnx.style().isClassName("cnxleft", cible)) var imagecopie�gauche = true;
				var copieLeft = cnx.zoom.realLeft; //position de la copie de l'image pour le zoom
				// var copieLeft = (imagecopieagauche) ? cnx.zoom.realLeft - cnx.zoom.actualWidth - decalage : cnx.zoom.realLeft + cnx.zoom.actualWidth + decalage; //position de la copie de l'image pour le zoom
				var copieTop = cnx.zoom.realTop - cnx.zoom.actualHeight - 5; //position de la copie de l'image pour le zoom
				/*var copieLeft = (imagecopie�gauche) ? cnx.zoom.realLeft - cnx.zoom.actualWidth - decalage : cnx.zoom.realLeft + cnx.zoom.actualWidth + decalage; //position de la copie de l'image pour le zoom
				var copieTop = cnx.zoom.realTop; //position de la copie de l'image pour le zoom*/
				
				/* cr�ation de la div qui contiendra la copie de l'image en grandeur r�elle */
				var copieDiv = document.getElementById("id_cnx_copiediv"); //teste si la <div> existe
				if (copieDiv == null) { //cr�er la <div> si elle n'existe pas encore
					var copieDiv = document.createElement("div"); //g�n�re un objet virtuel pour la div copie
					copieDiv.id = "id_cnx_copiediv"; //attribution d'un id
					copieDiv.className = "copiedivcnx"; //ajoute un style de type class en HTML
					copieDiv.style.left = copieLeft + "px"; //position la div copie
					copieDiv.style.top= copieTop + "px"; //position la div copie
					copieDiv.style.width = cnx.zoom.actualWidth +"px"; //dimension de la div copie
					copieDiv.style.height = cnx.zoom.actualHeight + "px"; //dimension de la div copie
					
					/* ins�re l'image en taille r�elle dans la div copie */
					var copieImg = new Image();// Declaration d'un objet Image
					copieImg.src = cible.src;// Affectation du chemin de l'image a l'objet
					copieImg.style.position = "absolute";
					copieImg.id = "id_cnx_copieimg"; //id de la copie de l'image
					
					cnx.dom().appendTo(copieDiv, copieImg); //ins�re l'image en taille r�elle dans la div copie
					cnx.dom().appendTo(document.body, copieDiv); //document.body.appendChild(copieDiv); //ins�re la div copie dans la page web
				}
					
				/* cr�ation de la div curseur qui entoure le curseur de la souris */
				var curseurDiv = document.getElementById("id_cnx_divcurseur"); //teste si la <div> existe
				if (curseurDiv == null) { //cr�er la <div> si elle n'existe pas encore
					var curseurDiv = document.createElement("div"); //g�n�re un objet virtuel pour la div curseur
					curseurDiv.className = "curseurcnx";
					curseurDiv.style.cursor = "crosshair";
					curseurDiv.id = "id_cnx_divcurseur";
					curseurDiv.style.backgroundColor = "#FFFFFF";
					cnx.dom().appendTo(document.body, curseurDiv); //document.body.appendChild(curseurDiv); //dessine la div curseur dans la page web
					cnx.style().setOpacity(30, curseurDiv); //opacit� � 30% - 0 => transparence totale - pour cet effet il faut un style type backgroundColor
				}
				
			}
		}, // }}}
		
		mouseout: function(e){ // ne d�tecte pas le out lors d'un mousewheel d'o� la v�rification dans mousemove {{{
			var cible = cnx.event().getTarget(e);
			if(cible.id == "id_cnx_divcurseur")	cnx.zoom.raz(); //teste si nous avons quitt� la div curseur - efface tous les param�tres
			return false;
		}, // }}}
		
		raz: function(){ // efface les param�tres si la souris sort de l'image cible{{{
			cnx.dom().removeElt("id_cnx_copieimg");//d�truit image copie - taille r�elle
			cnx.dom().removeElt("id_cnx_copiediv");//d�truit div copie
			cnx.dom().removeElt("id_cnx_divcurseur"); //d�truit la div autour du curseur de la souris
			
			cnx.zoom.iszoom = false; //contient l'image cible dont nous devons faire un effet zoom
			cnx.zoom.ratio = false; //ratio entre taille actuelle et taille r�elle de l'image
			cnx.zoom.actualWidth = false; //largeur actuelle de l'image cible
			cnx.zoom.actualHeight = false; //hauteur actuelle de l'image cible
			cnx.zoom.realLeft = false; //postion r�elle de l'image cible par rapport � la page web
			cnx.zoom.realTop = false; //postion r�elle de l'image cible par rapport � la page web
		}, // }}}
		
		mousemove: function(e){ // g�re  le zoom image {{{
			if (cnx.zoom.iszoom){ // teste si image zoom existe
				/**
				D�tecte si je suis toujours au-dessus de l'image ou de la div curseur
				si ce n'est pas le cas cnx.zoom.raz() et return pour quitter le programme
				n�cessaire car mouseout n'est pas actif lors d'un mousewheel - scrool roulette
				*/
				var cible = cnx.event().getTarget(e); //cible de l'event
				if (cible.id != "id_cnx_divcurseur" && cible != cnx.zoom.iszoom){ //je ne suis plus au-dessus de l'image - utile lors d'un mousewheel
					cnx.zoom.raz(); //efface tous les param�tres
					return false; // je quitte le programme
				}
				
				var cible = cnx.zoom.iszoom;
				x = cnx.event().pageScrollX(e); //left - position de la souris � l'�cran
				y = cnx.event().pageScrollY(e); //top - position de la souris � l'�cran
				
				/* dimension et position de la loupe curseur */
				var dim = cnx.style().getHeight(cible); //var dim = 100; dimension de la div autour du curseur
				cnx.style().setHeight(dim, "id_cnx_divcurseur"); //dimensionne la div qui suit le curseur
				cnx.style().setWidth(dim, "id_cnx_divcurseur"); //dimensionne la div qui suit le curseur
				var centre = dim / 2;
				var xLeft = x - centre;
				var yTop = y - centre;
				
				var maxLeft = cnx.zoom.realLeft + cnx.zoom.actualWidth - dim +2;
				if (xLeft > maxLeft)	xLeft = maxLeft; //bloque la div curseur dans l'image cible
				if(xLeft < cnx.zoom.realLeft)		xLeft = cnx.zoom.realLeft; //bloque la div curseur dans l'image cible
	
				var maxTop = cnx.zoom.realTop + cnx.zoom.actualHeight - dim + 2; //2 car cadre �paisseur 1px tout autour soit 1 en haut, 1 en bas => 2
				if (yTop > maxTop)	yTop = maxTop; //bloque la div curseur dans l'image cible
				if(yTop < cnx.zoom.realTop)		yTop = cnx.zoom.realTop;  //bloque la div curseur dans l'image cible
				
				var xLeft = cnx.style().setLeft(xLeft, "id_cnx_divcurseur"); //positionne la <div id="curseur"> de telle sorte que le pointer de la souris soit en son centre
				var yTop = cnx.style().setTop(yTop, "id_cnx_divcurseur"); //positionne la <div id="curseur"> de telle sorte que le pointer de la souris soit en son centre
				
				/*calcul du position de la souris par rapport � l'image cible pour l'effet zoom*/
				//cnx.surv("img ("+ cnx.zoom.realLeft +","+cnx.zoom.realTop + ") souris ("+x + ","+y+")"); //ligne de contr�le - alert()
				var relatif_left = cnx.zoom.realLeft - x; //distance entre bord gauche de l'image et la souris sur axe des x
				var relatif_top = cnx.zoom.realTop -y; //distance entre bord haut de l'image et la souris sur axe des y
				var dLeft = (relatif_left*(cnx.zoom.ratio-1)); //delta du d�placement de l'image en taille r�elle
				var dTop = (relatif_top*(cnx.zoom.ratio-1)); // pourquoi ratio-1?
				cnx.style().setLeft(dLeft, "id_cnx_copieimg"); //positionne l'image agrandie
				cnx.style().setTop(dTop, "id_cnx_copieimg"); //positionne l'image agrandie
			}
		}, // }}}
		
		author: "claudecnx jpconnexion" //derni�re instruction, ne pas mettre de virgule!
	}; //end of public section - return

})(); //end of cnx.zoom

var style_zoomcnx = ".copiedivcnx{border-color: #cccccc; border-style: solid; border-width: 1px;position: absolute; z-index: 5; overflow: hidden;}"; //�crit le style 
	style_zoomcnx += ".curseurcnx {border-color: #cccccc;	border-style: solid; border-width: 1px;	height: 150px; left: -75px;	position: absolute;	top: -75px;	width: 150px; z-index: 5;}";
	style_zoomcnx += ".cnxzoom {border-color: #cccccc; border-style: solid;	border-width: 1px;}"
cnx.style().appendStyle(style_zoomcnx); //ajoute le style className .copiedivcnx dans la balise <head>
	
cnx.event().addEvent("mouseover", cnx.zoom.mouseover, document); //onmouseover recherche image � zoomer
cnx.event().addEvent("mousemove", cnx.zoom.mousemove, document); //onmousemove fait deffiler l'image portant le zoom
cnx.event().addEvent("mouseout", cnx.zoom.mouseout, document); //onmouseout d�truit les donn�es m�moris�e pour annuler le zoom

})(); //end of  cnx.zoom - loupe

