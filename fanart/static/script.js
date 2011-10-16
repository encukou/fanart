$(function() {
    $('body').removeClass('no-js').addClass('have-js');
    deform.load();
});

$(function() {
    function resize() {
        if($(window).width() < $('#helper').width() - 5) {
            $('body').removeClass('wide').addClass('narrow');
        } else if($(window).width() > $('#helper').width() + 5) {
            $('body').removeClass('narrow').addClass('wide');
        }
        /*
        if($(window).height() < 500) {
            $('body').addClass('fullview');
        }else{
            $('body').removeClass('fullview');
        }
        */
    }
    $(window).bind("resize", resize);
    $('body').addClass('no-css-anim');
    resize();
    setTimeout(function() {$('body').removeClass('no-css-anim')}, 100);
});

/* Login */
/*
(function() {
    var pwd = $('#side_login li:has(input[type=password])');
    pwd.addClass('hidden').hide();
    function hide(element) {
        if (!pwd.hasClass('hidden')) {
            pwd.addClass('hidden').slideUp('fast');
        }
    }
    function show(element) {
        if (pwd.hasClass('hidden')) {
            pwd.removeClass('hidden').slideDown('fast');
        }
    }
    function username_change() {
        if ($(this).val() == '') {
            hide(pwd);
        }else{
            show(pwd);
        }
    }
    $('#side_login input[type=text]').change(username_change).keypress(username_change).
        keydown(username_change).keyup(username_change).click(username_change).
        click();
});
*/

function fade_flashes() {
    console.log($('.flash:not(.faded)'))
    $('.flash:not(.faded)').addClass('faded')
}
$(function() {setTimeout(fade_flashes, 100)});
