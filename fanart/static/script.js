$(function() {
    $('body').removeClass('no-js').addClass('have-js');
    deform.load();
    $.fanart = {
        csrft: $("#csrft").val(),
        api_base: $("#api_base").val(),
    }
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
    $('.flash:not(.faded)').addClass('faded')
}
$(function() {setTimeout(fade_flashes, 100)});

/* Preview */
$(function() {
    $("textarea.markdown-textarea").each(function (index, md_textarea) {
        var preview_div = $("<div class='markdown preview'></div>");
        preview_div.insertAfter(md_textarea);
        var timer_id = 0;
        var state = 'ready'; // idle state
        // -> 'warmup' - document changed; wait for small period of inactivity before AJAX request
        // -> 'request' - the AJAX request is executing
        // -> 'cooldown' - a rather large timeout after the AJAX request is acive; for rate limiting
        var last_data = '';
        function do_ajax() {
            state = 'request';
            var request_data = $(md_textarea).val();
            function done(cooldown_timeout) {
                state = 'cooldown';
                changed();
                timer_id = setTimeout(function() {
                    state = 'ready';
                    changed();
                }, cooldown_timeout);
            };
            function success(data, textStatus, jqXHR) {
                preview_div.empty();
                preview_div.append(data);
                last_data = request_data;
                done(2000);
            };
            if (request_data) {
                $.ajax({
                    type: 'POST',
                    dataType: 'html',
                    data: {
                        data: request_data,
                        csrft: $.fanart.csrft
                    },
                    url: $.fanart.api_base + '/markdown',
                    error: function(jqXHR, textStatus, errorThrown) {
                        done(10000);
                    },
                    success: success
                });
            }else{
                success('', '', '');
            }
        }
        function changed() {
            if (last_data == $(md_textarea).val()) {
                preview_div.removeClass('out-of-date');
            }else{
                preview_div.addClass('out-of-date');
                if (state == 'ready') {
                    timer_id = setTimeout(do_ajax, 400);
                    state = 'warmup';
                }else if (state == 'warmup') {
                    clearTimeout(timer_id);
                    timer_id = setTimeout(do_ajax, 400);
                }
            }
        }
        $(md_textarea).change(changed).keypress(changed).keydown(changed).
            keyup(changed).click(changed);
    });
});
