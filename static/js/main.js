
// initialize global variables
var paused = false;
var timeElapsed = 0;
var timerID = -1;

// set the dimensions
function set_dims(width, height, selector) {
    var max_dims = [0.5 * $(document).width(), 0.5 * $(document).height()];
    if (width > max_dims[0]) {
        selector.css("width", max_dims[0]);
        selector.css("height", max_dims[0] * height / width);
    } else if (height > max_dims[1]) {
        selector.css("width", max_dims[1] * width / height);
        selector.css("height", max_dims[1]);
    } else {
        selector.css("width", width);
        selector.css("height", height);
    }
}

// initialize a plot
function init_img(url, container) {
    var max_dims = [0.5 * $(document).width(), 0.5 * $(document).height()];
    var selector = $("#" + container);
    $("<img/>").attr("src", url).on("load", function () {
        set_dims(this.width, this.height, selector)
        selector.resizable({
            aspectRatio: true,
            maxHeight: max_dims[1],
            maxWidth: max_dims[0],
            minHeight: 30,
            minWidth: 30,
            containment: "#plots-container",
            autoHide: true,
            handles: "n, e, s, w"
        });
        selector.css("background-image", "url('" + url + "')");
        selector.data("url", url);
        selector.draggable({
            snap: ".plot-container.visible, .table-container.visible",
            containment: "#plots-container"
        });
        selector.css("position", "absolute");
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
}

function update_img(url, container) {
    var current_width = $("#" + container).width();
    var selector = $("#" + container);
    $("<img/>").attr("src", url).on("load", function () {
        set_dims(current_width, current_width * this.height / this.width, selector);
        selector.css("background-image", "url('" + url + "')");
        selector.data("url", url);
    });
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

// toggle visibility for plots and data tables
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
});

// toggle visibility for all plots and data tables from a routine
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

// bring to the front with a double click
$("#plots-container").on("dblclick", ".plot-container, .table-container", function () {
    $(this).parent().append($(this));
});

// create period handle
var handle = $("#custom-handle");
$("#slider").slider({
    min: -1,
    max: 2,
    step: 0.001,
    create: function() {
        handle.children().val(Math.pow(10, parseFloat($(this).slider("value"))).toPrecision(3));
        },
    slide: function(event, ui) {
        handle.children().val(Math.pow(10, parseFloat(ui.value)).toPrecision(3));
    }
});

// change slider value on handle change
handle.children().on("change", function () {
    $("#slider").slider("value", Math.log10(parseFloat($(this).val())));
});

// highlight an item if hovering in plot list
$("#plot-list").on("mouseenter mouseleave", ".plot-list-item", function () {
    var plot_id = $(this).data("id");
    $("#" + plot_id).toggleClass("highlight");
});

// highlight all items in routine if hovering in plot list
$("#plot-list").on("mouseenter mouseleave", ".plot-list-routine-title", function () {
    $(this).siblings(".plot-list-item").each(function() {
        var plot_id = $(this).data("id");
        $("#" + plot_id).toggleClass("highlight");
    });
});
