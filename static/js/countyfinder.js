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



    function openNav() {
        document.getElementById("myNav").style.height = "calc(100% - 40px)";
      }
      
      function closeNav() {
        document.getElementById("myNav").style.height = "0%";
      }