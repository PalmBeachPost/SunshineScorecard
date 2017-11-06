var $ = jQuery
$(document).ready(function () {
    $('#select-anchor').change( function () {
        var targetPosition = $($(this).val()).offset().top-50;
        $('html,body').animate({ scrollTop: targetPosition}, 'medium');
    });
});
