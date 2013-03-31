"use strict";

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
        changed();
    });
});

/* Details */
$(function() {
    $('body').addClass($.fn.details.support ? 'details' : 'no-details');
    $('details').details();
});

/* Fuzzy dates */
$(function() {
    $.timeago.inWords = function(distanceMillis, element, orig_date) {
        if (typeof orig_date === 'undefined') {
            orig_date = new Date((new Date()).getTime() - distanceMillis);
        }
        var $l = this.settings.strings;
        var prefix = $l.prefixAgo;
        var suffix = $l.suffixAgo;
        if (this.settings.allowFuture) {
            if (distanceMillis < 0) {
                prefix = $l.prefixFromNow;
                suffix = $l.suffixFromNow;
            }
        }

        var seconds = Math.abs(distanceMillis) / 1000;
        var minutes = seconds / 60;
        var hours = minutes / 60;
        var days = hours / 24;
        var weeks = weeks / 24;
        var months = days / 30.5;
        var years = days / 365;

        function pad2(n) {
            var z = '0';
            var n = n + '';
            var width = 2;
            return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
        }
        if (element && element.attr('data-dateformat') == 'compact') {
            if (days < 2) {
                var today = new Date();
                if (orig_date.getDate() == today.getDate()) {
                    return pad2(orig_date.getHours()) + ':' + pad2(orig_date.getMinutes());
                }
                var yesterday = today;
                yesterday.setDate(yesterday.getDate() - 1);
                if (orig_date.getDate() == yesterday.getDate()) {
                    return "včera";
                }
                var tomorrow = today;
                tomorrow.setDate(tomorrow.getDate() + 1);
                if (orig_date.getDate() == tomorrow.getDate()) {
                    return "zítra";
                }
            }
            var month_day = pad2(orig_date.getDate()) + '. ' + pad2(orig_date.getMonth())
            if (orig_date.getYear() == today.getYear()) {
                return month_day;
            }
            return month_day + '. ' + orig_date.getYear();
        }

        function substitute(stringOrFunction, number) {
            var string = $.isFunction(stringOrFunction) ? stringOrFunction(number, distanceMillis) : stringOrFunction;
            var value = ($l.numbers && $l.numbers[number]) || number;
            var substituted = string.replace(/%d/i, value);
            return $.trim([prefix, substituted, suffix].join($l.wordSeparator));
        }

        var future = distanceMillis < 0;
        function simple(past_str, future_str) {
            if (future) return future_str;
            return past_str;
        }
        function complex(value, past, future_2, future_5) {
            value = Math.round(value);
            if (!future) return past.replace(/%d/i, value);
            if (value < 5) return future_2.replace(/%d/i, value);
            return future_5.replace(/%d/i, value);
        }

        if (seconds < 45) return simple("před chvilkou", "za chvilku");
        if (seconds < 90) return simple("před minutou", "za minutu");
        if (minutes < 10) return complex(minutes, "před %d minutami", "za %d minuty", "za %d minut");
        if (minutes < 20) return simple("před čtvrt hodinou", "za čtvrt hodiny");
        if (minutes < 45) return simple("před půl hodinou", "za půl hodiny");
        if (minutes < 90) return simple("před hodinou", "za hodinu");
        if (hours < 20) return complex(hours, "před %d hodinami", "za %d hodiny", "za %d hodin");
        if (days < 2) {
            var relative = new Date();
            if (future) {
                relative.setDate(relative.getDate() + 1);
                if (orig_date.getDate() == relative.getDate()) return "zítra";
            } else {
                relative.setDate(relative.getDate() - 1);
                if (orig_date.getDate() == relative.getDate()) return "včera";
            }
        }
        if (hours < 42) return simple("před 1 dnem", "za 1 den");
        if (days < 6) return complex(days, "před %d dny", "za %d dny", "za %d dní");
        if (days < 8) return simple("před týdnem", "za týden");
        if (weeks < 3.5) return complex(weeks, "před %s týdny", "za %s týdny", "za %s týdnů");
        if (months < 2) {
            var relative = new Date();
            if (future) {
                relative.setMonth(relative.getMonth() + 1);
                if (orig_date.getMonth() == relative.getMonth()) return "příští měsíc";
            } else {
                relative.setMonth(relative.getMonth() - 1);
                if (orig_date.getMonth() == relative.getMonth()) return "minulý měsíc";
            }
        }
        if (days < 45) return simple("před měsícem", "za měsíc");
        if (months < 14) return complex(months, "před %d měsíci", "za %d měsíce", "za %d měsíců");
        if (years < 2) {
            var relative = new Date();
            if (future) {
                relative.setYear(relative.getYear() + 1);
                if (orig_date.getYear() == relative.getYear()) return "příští rok";
            } else {
                relative.setYear(relative.getYear() - 1);
                if (orig_date.getYear() == relative.getYear()) return "loni";
            }
        }
        if (years < 1.5) return simple("před rokem", "za rok");
        return complex(years, "před %d lety", "za %d roky", "za %d let");

    };
    jQuery("time").timeago();
});

/* AJAX Update */
$(function() {
    function load(container, data) {
        data.each(function() {
            var item = $(this);
            var id = item.attr('data-id');
            var max_length = container.attr('data-max-length');
            if (!container.find('*[data-id=' + id + ']').length) {
                var time = item.attr('data-time')
                var previous = null;
                container.find('*[data-time]').each(function() {
                    if ($(this).attr('data-time') < time) {
                        previous = $(this);
                        return false;
                    }
                });
                item.hide();
                if (previous === null) {
                    container.prepend(item);
                } else {
                    previous.before(item);
                }
                item.addClass('ajax-loaded');
                item.slideDown("slow");
            };
            if (max_length) {
                container.find('*[data-time]').slice(max_length).slideUp(
                    "slow",
                    function() { $(this).remove(); });
            }
        });
    };
    function do_update() {
        var container = $('*[data-update-stream]').first();
        var url = $.fanart.api_base + '/' + container.attr('data-update-stream');
        var since = container.find('*[data-time]').first().attr('data-time');
        $.ajax({
            url: url,
            data: {since: since},
            dataType: 'html',
            ifModified: true,
            success: function (data, status, jqXHR) {
                load(container, $(data));
                set_timer(15000);
            },
            error: function (jqXHR, textStatus, errorThrown) {
                set_timer(60000);
            }
        });
    };
    var timer_id = null;
    function set_timer(n) {
        if (timer_id !== null) {
            clearTimeout(timer_id);
            timer_id = null;
        }
        timer_id = setTimeout(do_update, n);
    }
    set_timer(15);
});
