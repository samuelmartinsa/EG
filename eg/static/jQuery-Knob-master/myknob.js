function mydial(maxDial,curDial){
    if($("#alternativedial").length > 0) {
        $("#alternativedial").html("Remaining time : <br> " + curDial + " out of " + maxDial);
    }
    $("#dial").knob({
        'min':0
        ,'max':maxDial
        ,'readOnly':true
        , 'height':120
        , 'width':120
        });
    $("#dial").val(curDial);
    //var canvas = document.querySelector('canvas');
    //canvas.style.width ='200px';
    //canvas.style.height ='200px';
}