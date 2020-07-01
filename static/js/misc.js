
// revert analysis options when routine selection changes
$(".filetree").on("click", ".tree-item.routine, .main-item.routine", function () {
    $(".routine-info").css("display", "inline");
    if (!$(this).hasClass("selected")) {
        $("#revert-analysis").trigger("click");
        Sijax.request("display_routine_info", [$(this).text()]);
    }
    $("#shots-choice").select2({
        maximumSelectionLength: parseInt($("#num-shots").val(), 10)
    });
    $("#filetype").select2({
        tags: true
    });
});

// reset all routine information when routine selection changes
$(".tree, .main-tree, #unselect, .tree-item.support, .main-item.support").on("click", function(){
    reset_routine_info();
});

// reset routine information
function reset_routine_info() {
    $(".routine-info").css("display", "none");
}

// select the data directory
$("#select-data-dir").click(function() {
    var routine_name = $(".selected").length > 0 ? $(".selected").text(): "";
    var data_dir = prompt("Absolute path to shots directory (type 'reset' to reset)");
    var update_dir_options = $(".selected").hasClass("main-item routine") || $(".selected").hasClass("tree-item routine");
    Sijax.request("select_data_dir", [data_dir, update_dir_options, routine_name]);
});

// select the shots directory
$("#shots-dir-options").on("change", function () {
    var routine_name = $(".selected").text();
    var shots_dir = Sijax.getFormValues("#routine-shots-dir");
    Sijax.request("set_shots_dir", [routine_name, shots_dir]);
});

// select the read-write json file
$("#json-options").on("change", function () {
    var routine_name = $(".selected").text();
    var json_file = Sijax.getFormValues("#routine-json");
    Sijax.request("set_json_options", [routine_name, json_file]);
});

// revert the analysis options (i.e. undo changes)
$("#revert-analysis").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        var routine_name = $(".selected").text();
        Sijax.request("refresh_analysis", [routine_name]);
        deactivate_buttons("#update-analysis, #revert-analysis");
    }
});

// update which analysis options are available
function check_shots_display() {
    var select = document.getElementById("select-shots-by");
    var selected_method = select.options[select.selectedIndex].value;
    if (selected_method === "choice") {
        $("#shots-choice-container").show();
        $("#filetype-container").hide();
    } else {
        $("#shots-choice-container").hide();
        $("#filetype-container").show();
    }
    var methods_no_num_shots = ["all", "new", "modified"];
    if (methods_no_num_shots.indexOf(selected_method) >= 0) {
        $("#num-shots-container").hide();
    } else {
        $("#num-shots-container").show();
    }
}

// change the number of shots
$("#num-shots").on("change", function() {
    $("#shots-choice").val(null);
    $("#shots-choice").select2({
        maximumSelectionLength: parseInt($("#num-shots").val(), 10)
    });
});

// update analysis options
$("#update-analysis").on("click", function () {
    if (!$(this).hasClass("inactive")) {
        var routine_name = $(".selected").text();
        var analysis_options = Sijax.getFormValues("#analysis-options");
        var shots_choice = $("#shots-choice").select2("data");
        var filetype = $("#filetype").select2("data");
        Sijax.request("update_analysis", [routine_name, analysis_options, shots_choice, filetype]);
        deactivate_buttons("#update-analysis, #revert-analysis");
    }
});

// active buttons
function activate_buttons(button_selector) {
    $(button_selector).removeClass("inactive");
}

// deactivate buttons
function deactivate_buttons(button_selector) {
    $(button_selector).addClass("inactive");
}

// change available analysis options based on current analysis options
$("#select-shots-by, #num-shots, #shots-choice, #frequency, #filetype").on("change", function () {
    activate_buttons("#update-analysis, #revert-analysis");
    check_shots_display();
});

function select_filetype(filetypes) {
    $("#filetype").val(filetypes);
    $("#filetype").trigger("change");
    deactivate_buttons("#update-analysis, #revert-analysis");
}