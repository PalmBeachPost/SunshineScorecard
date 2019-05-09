var $ = jQuery
$(document).ready(function () {
    $('#select-anchor').change( function () {
        var targetPosition = $($(this).val()).offset().top + 25;
        console.log(targetPosition);
        $('html,body').animate({ scrollTop: targetPosition}, 1000);
    });
});


function myFunction() {
    var x = document.getElementById("myTopnav");
        if (x.className === "navmen") {
            x.className += " showmen";
        } else {
            x.className = "navmen";
          }
    };


    $(document).ready(function(){
        $(document).scroll(function() {
            var alpha = Math.min(0 + 0.4 * $(this).scrollTop() / 210, 1);
            var channel = Math.round(alpha * 255);
            $(".topnav").css('background-color', 'rgb(' + channel + ',' + channel + ',' + channel + ')');
        });
    });