
// initialize global variables
var paused = false; // whether analysis was just paused
var timeElapsed = 0; // time elapsed on timer
var timerID = -1;
var max_dims = [0.5 * $(document).width(), 0.5 * $(document).height()]; // maximum plot size
var ctrl_pressed = false;

$(document).ready(function () {
    $("#plots-container").sortable({
        containment: "#plots-container"
    });
    $("#plots-container").sortable("disable");
    $("#routine-list").selectableScroll({
        scrollSnapX: 5,
        scrollAmount: 25,
        selected: function(event, ui) {
            update_routine_buttons();
        }, stop: function(event, ui) {
            update_routine_buttons();
        }
    });
});

// set the dimensions
function set_dims(width, height, selector) {
    var ratio = Math.min(max_dims[0] / width, max_dims[1] / height, 1);
    selector.width(width * ratio);
    selector.height(height * ratio);
}

// enable grid for a plot
function grid_on(selector) {
    selector.draggable("disable");
    selector.css("position", "initial");
    selector.css("top", "initial");
    selector.css("left", "initial");
}

// disable grid for a plot
function grid_off(selector) {
    selector.each(function () {
        var pos = $(this).position();
        $(this).css("top", pos.top);
        $(this).css("left", pos.left);
    });
    selector.draggable("enable");
    selector.css("position", "absolute");
}

// initialize a plot
function init_img(url, container) {

    var selector = $("#" + container);
    $("<img/>").attr("src", url).on("load", function () {
        set_dims(this.width / 2, this.height / 2, selector);
        selector.resizable({
            aspectRatio: true,
            maxHeight: max_dims[1],
            maxWidth: max_dims[0],
            minHeight: 30,
            minWidth: 30,
            containment: "#plots-container",
            autoHide: true,
            handles: "n, e, s, w",
            stop: function() {
                if ($("#toggle-grid").hasClass("on")) {
                    $("#toggle-grid").trigger("click");
                    $("#toggle-grid").trigger("click");
                }
            },
            resize: function() {
                update_grid_slider();
            }
        });
        selector.css("background-image", "url('" + url + "')");
        selector.data("url", url);
        selector.draggable({
            snap: ".plot-container.visible, .table-container.visible",
            containment: "#plots-container"
        });
        selector.css("position", "absolute");
        if ($("#toggle-grid").hasClass("on")) {
            grid_on(selector);
        }
        update_grid_slider();
    });
}

// initialize a data table
function init_table(container) {
    var selector = $("#" + container);
    selector.draggable({
        snap: ".plot-container.visible, .table-container.visible",
        containment: "#plots-container"
    });
    selector.css("position", "absolute");
    if ($("#toggle-grid").hasClass("on")) {
        grid_on(selector);
    }
}

// update a plot
function update_img(url, container) {
    var current_width = $("#" + container).width();
    var selector = $("#" + container);
    $("<img/>").attr("src", url).on("load", function () {
        set_dims(current_width, current_width * this.height / this.width, selector);
        selector.css("background-image", "url('" + url + "')");
        selector.data("url", url);
    });
    update_grid_slider();
}

// start the analysis
$("#start-analysis").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        var period = parseFloat($("#period").val());
        sjxComet.request("analyse", [paused, period]);
        $("#start-analysis").addClass("inactive");
        $("#stop-analysis, #pause-analysis").removeClass("inactive");
        $("#slider").slider("disable");
    }
});

// pause the analysis
$("#pause-analysis").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        paused = true;
        Sijax.request("pause_analysis");
        $("#start-analysis").removeClass("inactive");
        $("#pause-analysis").addClass("inactive");
        $("#slider").slider("enable");
    }
});

// stop the analysis
$("#stop-analysis").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        paused = false;
        Sijax.request("stop_analysis");
        $("#start-analysis").removeClass("inactive");
        $("#stop-analysis, #pause-analysis").addClass("inactive");
        $("#slider").slider("enable");
    }
});

// return a formatted time string
function get_time(seconds) {
    var days = Math.floor(seconds / 86400);
    var hours = Math.floor((seconds % 86400) / 3600) < 10 ? "0" + Math.floor((seconds % 86400) / 3600): Math.floor((seconds % 86400) / 3600);
    var minutes = Math.floor((seconds % 3600) / 60) < 10 ? "0" + Math.floor((seconds % 3600) / 60): Math.floor((seconds % 3600) / 60);
    var seconds_rounded = (seconds % 60) < 10 ? "0" + (seconds % 60).toFixed(2): (seconds % 60).toFixed(2);
    var time;
    if (days > 0) {
        time = days + ":" + hours + ":" + minutes + ":" + seconds_rounded;
    } else if (hours > 0) {
        time = hours + ":" + minutes + ":" + seconds_rounded;
    } else if (minutes > 0) {
        time = minutes + ":" + seconds_rounded;
    } else {
        time = seconds_rounded;
    }
    return time;
}

// increment the elapsed time
function tick() {
    timeElapsed += 0.01;
    $("#timer").html(get_time(timeElapsed));
}

// start the timer
function start_timer() {
    if (timerID === -1) {
        timerID = setInterval(tick, 10);
    }
}

// stop the timer
function stop_timer() {
    if(timerID !== -1) {
        clearInterval(timerID);
        timerID = -1;
    }
}

// reset the timer
function reset_timer() {
    stop_timer();
    timeElapsed = -0.01;
}

// toggle visibility for plots
$("#plot-list").on("click", ".plot-list-item", function () {
    var plot_id = $(this).data("id");
    var plot_selector = $("#" + plot_id);
    if ($(this).hasClass("invisible")) {
        plot_selector.show();
        plot_selector.parent().append(plot_selector);
        if ($(this).siblings(".plot-list-routine-title").hasClass("invisible")) {
            $(this).siblings(".plot-list-routine-title").removeClass("invisible");
            $(this).siblings(".plot-list-routine-title").addClass("visible");
        }
    } else {
        $("#" + plot_id).hide();
        if (!$(this).siblings(".plot-list-routine-title").hasClass("invisible") && !$(this).siblings(".plot-list-item").hasClass("visible")) {
            $(this).siblings(".plot-list-routine-title").removeClass("visible");
            $(this).siblings(".plot-list-routine-title").addClass("invisible");
        }
    }
    plot_selector.toggleClass("visible");
    $(this).toggleClass("invisible");
    $(this).toggleClass("visible");
    update_grid_slider();
});

// toggle visibility for all plots from a routine
$("#plot-list").on("click", ".plot-list-routine-title", function () {
    var invisible = $(this).hasClass("invisible");
    $(this).siblings(".plot-list-item").each(function() {
        var plot_id = $(this).data("id");
        if (invisible) {
            $("#" + plot_id).show();
            $(this).removeClass("invisible");
            $(this).addClass("visible");
        } else {
            $("#" + plot_id).hide();
            $(this).removeClass("visible");
            $(this).addClass("invisible");
        }
    });
    $(this).toggleClass("visible");
    $(this).toggleClass("invisible");
    update_grid_slider();
});

// bring plot to front with a double click
$("#plots-container").on("dblclick", ".plot-container, .table-container", function () {
    $(this).parent().append($(this));
});

// period slider
var handle = $("#custom-handle");
$("#slider").slider({
    min: -1,
    max: 2,
    step: 0.001,
    create: function() {
        handle.children().val(Math.pow(10, parseFloat($("#slider").slider("value"))).toPrecision(3));
        },
    slide: function(event, ui) {
        handle.children().val(Math.pow(10, parseFloat(ui.value)).toPrecision(3));
    }
});

// change slider value on handle change
handle.children().on("change", function () {
    $("#slider").slider("value", Math.log10(parseFloat($(this).val())));
});

// grid slider
$("#slider-grid").slider({
    orientation: "vertical",
    min: 30,
    max: Math.min(max_dims[0], max_dims[1]),
    step: 1,
    slide: function(event, ui) {
        $(".plot-container").each(function () {
            set_dims(ui.value * $(this).width() / $(this).height(), ui.value, $(this));
        });
    }
});

// update grid slider value
function update_grid_slider() {
    var num = $(".plot-container.visible").length;
    if (num === 0) {
        $("#slider-grid").slider("value", 30);
    } else {
        var tot_height = 0;
        $(".plot-container.visible").each(function () {
            tot_height += $(this).height();
        });
        $("#slider-grid").slider("value", tot_height / num);
    }
}

// highlight corresponding plot if hovering over item in plot list
$("#plot-list").on("mouseenter mouseleave", ".plot-list-item", function () {
    var plot_id = $(this).data("id");
    $("#" + plot_id).toggleClass("highlight");
});

// highlight all corresponding plots in routine if hovering in plot list
$("#plot-list").on("mouseenter mouseleave", ".plot-list-routine-title", function () {
    $(this).siblings(".plot-list-item").each(function() {
        var plot_id = $(this).data("id");
        $("#" + plot_id).toggleClass("highlight");
    });
});

// toggle grid functionality
$("#toggle-grid").on("click", function () {
    $(this).toggleClass("on");
    var all_containers = $(".plot-container, .table-container");
    if ($(this).hasClass("on")) {
        $(this).text("grid_on");
        $("#plots-container").sortable("enable");
        grid_on(all_containers);
    } else {
        $(this).text("grid_off");
        $("#plots-container").sortable("disable");
        grid_off(all_containers);
    }
});

$("#remove-routine").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        var selected_files = $("#routine-list .ui-selected").map(function() {
            $(this).remove();
            return this.id;
        }).get();
        Sijax.request("remove_routine", [selected_files]);
        update_routine_buttons();
    }
});

function unselect() {
    $(".ui-selected").removeClass("ui-selected");
    update_routine_buttons();
}

$("#toggle-select").on("click", function () {
    $(this).toggleClass("checked");
    if ($(this).hasClass("checked")) {
        $("#routine-list li").addClass("ui-selected");
        $(this).text("check_box");
        update_routine_buttons();
    } else {
        $(this).text("check_box_outline_blank");
        unselect();
    }
});

window.addEventListener("keyup", function (event) {
    if (event.defaultPrevented) {
        return;
    }
    switch (event.key) {
        case "Meta":
           ctrl_pressed = false;
           break;
        default:
            return;
    }
});

window.addEventListener("keydown", function (event) {
    if (event.defaultPrevented) {
        return;
    }
    switch (event.key) {
        case "Escape": // unselect items
            unselect();
            event.preventDefault();
            break;
        case "4":
            if (ctrl_pressed) {
                $("#run-routine").trigger("click");
                event.preventDefault();
                break;
            } else {
                return;
            }
        case "Meta":
            ctrl_pressed = true;
            return;
        default:
            return;
    }
});


$("#filter").on("keyup", function() {
    unselect();
    var filter = $(this).val();
    $(".routine").show();
    $(".routine").each(function () {
        var filename = $(this).text();
        if (filename.indexOf(filter) === -1) {
            $(this).hide();
        }
    });
});

$("#run-routine").on("click", function() {
    if (!$(this).hasClass("inactive")) {
        $("#routine-list .ui-selected").each(function () {
            if (!$(this).hasClass("running")) {
                $(this).removeClass("error");
                $(this).addClass("running");
                $("#status").append("Running '" + $(this).text() + "'.<br>");
                Sijax.request("run_routine", [this.id]);
            }
        });
        update_routine_buttons();
    }
});

$("#stop-routine").on("click", function() {
    if (!$(this).hasClass("inactive")) {
        var selected_files = $("#routine-list .ui-selected").map(function() {
            return this.id;
        }).get();
        Sijax.request("stop_routine", [selected_files]);
        update_routine_buttons();
    }
});

$("#slider-status-size").slider({
    orientation: "vertical",
    min: 6,
    max: 24,
    step: 0.1,
    value: 16,
    slide: function(event, ui) {
        $("#status").css("font-size", ui.value);
    }
});

function adjust_routine_class(id, error) {
    var routine = $("#" + id);
    routine.removeClass("running");
    if (error) {
        routine.addClass("error");
    }
    update_routine_buttons();
}

function update_routine_buttons() {
    var selected = $("#routine-list .ui-selected");
    if (selected.length === 0) {
        $("#remove-routine").addClass("inactive");
        $("#toggle-select").removeClass("checked");
        $("#toggle-select").text("check_box_outline_blank");
    } else {
        $("#remove-routine").removeClass("inactive");
        $("#toggle-select").addClass("checked");
        $("#toggle-select").text("check_box");
    }
    if (selected.hasClass("running")) {
        $("#stop-routine").removeClass("inactive"); // some selected routines running
    } else {
        $("#stop-routine").addClass("inactive"); // all selected routines not running
    }
    if (selected.not(".running").length > 0) {
        $("#run-routine").removeClass("inactive"); // some selected routines not running
    } else {
        $("#run-routine").addClass("inactive"); // all selected routines running
    }
}

$(window).bind("beforeunload", function() {
    var all_files = $("#routine-list").children().map(function() {
        return this.id;
    }).get();
    Sijax.request("stop_routine", [all_files]);
});
