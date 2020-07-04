
// initialize global variables
var paused = false;
var timeElapsed = 0;
var timerID = -1;

// go to the analysis settings page
$("#to-analysis").on("click", function () {
    stop_analysis();
    location.href="/";
});

// set the dimensions for the container
function set_dims(object, container, factor) {
    var window_dims = [0.95 * $(window).width(), 0.95 * $(window).height()];
    var dims = [object.width * factor, object.height * factor];
    if (dims[0] > window_dims[0]) {
        $("#" + container).css("width", window_dims[0]);
        $("#" + container).css("height", window_dims[0] * dims[1] / dims[0]);
    } else if (dims[1] > window_dims[1]) {
        $("#" + container).css("width", window_dims[1] * dims[0] / dims[1]);
        $("#" + container).css("height", window_dims[1]);
    } else {
        $("#" + container).css("width", dims[0]);
        $("#" + container).css("height", dims[1]);
    }
}

// initialize a plot
function init_img(url, container) {
    var window_dims = [0.95 * $(window).width(), 0.95 * $(window).height()];
    $("<img/>").attr("src", url).on("load", function () {
        set_dims(this, container, 1);
        $("#" + container).resizable({
            aspectRatio: true,
            maxHeight: window_dims[1],
            maxWidth: window_dims[0],
            minHeight: 30,
            minWidth: 30,
            containment: "#plots-container",
            autoHide: true,
            handles: "n, e, s, w"
        });
        $("#" + container).css("background-image", "url('" + url + "')");
        $("#" + container).data("url", url);
        $("#" + container).data("width", $("#" + container).width());
        $("#" + container).draggable({
            snap: ".plot-container.visible, .table-container.visible",
            containment: "#plots-container"
        });
        $("#" + container).css("position", "absolute");
    });
}

// initialize a data table
function init_table(container) {
    $("#" + container).draggable({
        snap: ".plot-container.visible, .table-container.visible",
        containment: "#plots-container"
    });
    $("#" + container).css("position", "absolute");
}

// update a plot
function update_img(url, container, keep_size) {
    var factor = keep_size === "true" ? $("#" + container).width() / $("#" + container).data("width"): 1;
    $("<img/>").attr("src", url).on("load", function () {
        set_dims(this, container, factor);
        $("#" + container).css("background-image", "url('" + url + "')");
        $("#" + container).data("url", url);
    });
}

// start the analysis
$("#start-analysis").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        Sijax.request("analyse", [paused]);
        $("#start-analysis").addClass("inactive");
        $("#stop-analysis").removeClass("inactive");
        $("#pause-analysis").removeClass("inactive");
    }
});

// pause the analysis
$("#pause-analysis").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        paused = true;
        Sijax.request("pause_analysis");
        $("#start-analysis").removeClass("inactive");
        $("#pause-analysis").addClass("inactive");
    }
});

// request analyse_routine
function make_comet_request(data_dir, routine, period) {
    sjxComet.request("analyse_routine", [data_dir, routine, period]);
}

// stop the analysis
function stop_analysis() {
    paused = false;
    Sijax.request("stop_analysis");
    $("#start-analysis").removeClass("inactive");
    $("#stop-analysis").addClass("inactive");
    $("#pause-analysis").addClass("inactive");
}

$("#stop-analysis").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        stop_analysis();
    }
});

// return a formatted string from seconds elapsed
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
    if (timerID == -1) {
        timerID = setInterval(tick, 10);
    }
}

// stop the timer
function stop_timer() {
    if(timerID != -1) {
        clearInterval(timerID);
        timerID = -1;
    }
}

// reset the timer
function reset_timer() {
    stop_timer();
    timeElapsed = -0.01;
}

// toggle visibility for plots and data tables
$("#plot-list").on("click", ".plot-list-item", function () {
    var plot_id = $(this).data("id");
    if ($(this).hasClass("invisible")) {
        $("#" + plot_id).show();
        $("#" + plot_id).parent().append($("#" + plot_id));
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
    $("#" + plot_id).toggleClass("visible");
    $(this).toggleClass("invisible");
    $(this).toggleClass("visible");
});

// toggle visibility for all plots and data tables in a routine
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
});

// bring a plot or data table to the front with a double click
$("#plots-container").on("dblclick", ".plot-container, .table-container", function () {
    $(this).parent().append($(this));
});