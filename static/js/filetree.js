
$(document).ready(function () {
    $("body").find(".tree").fadeOut(0); // make all tree items invisible
    $("#path").attr("value", get_selected_path()); // initialize path in form
});

// open and close folders
$(".filetree").on("click", ".tree-title.selected", function(){
    setStatus($(this));
});

// select items
$(".filetree").on("click", ".tree-title, .tree-item, .main-item", function(){
    $(".selected").removeClass("selected");
    $(this).addClass("selected");
    $("#path").attr("value", get_selected_path());
    $("#remove, #unselect").removeClass("inactive");
});

// unselect items
$("#unselect").click(function(){
    $(".selected").removeClass("selected");
    $("#path").attr("value", get_selected_path());
    $("#remove, #unselect, #update-analysis").addClass("inactive");
});

// add key listeners
window.addEventListener("keydown", function (event) {
    if (event.defaultPrevented) {
    return;
  }
  switch (event.key) {
    case "ArrowDown":
      break;
    case "ArrowUp":
      break;
    case "Escape": // unselect items
        $(".selected").removeClass("selected");
        $("#path").attr("value", get_selected_path());
        $("#remove, #unselect, #update-analysis").addClass("inactive");
        reset_routine_info();
      break;
    default:
      return;
  }
  event.preventDefault();
}, true);

// create a new folder
$("#new_folder").click(function () {
    var folder_name = prompt("Folder name");
    if (folder_name) {
        var folder_path = get_selected_path();
        Sijax.request("add_folder", [folder_path, folder_name]);
        var folder_element = document.createElement("UL");
        var folder_title_element = document.createElement("LI");
        var folder_text = document.createTextNode(folder_name);
        folder_title_element.appendChild(folder_text);
        folder_title_element.className = "tree-title";
        folder_title_element.dataset.path = folder_path === "" ? folder_name: folder_path + "/" + folder_name;
        if (folder_path === "") {
            folder_element.className = "main-tree";
            document.getElementsByClassName("filetree")[0].appendChild(folder_element);
        } else {
            folder_element.className = "tree";
            document.getElementsByClassName("selected")[0].parentElement.appendChild(folder_element);
            if (!$(".selected").hasClass("active")) {
                setStatus($(".selected"));
            }
        }
        folder_element.appendChild(folder_title_element);
        $("#status").append("Folder '" + folder_name + "' added succesfully<br/>");
    } else {
        $("#status").append("No folder name given<br/>");
    }
});

// remove item
$("#remove").click(function () {
    var path = get_selected_path();
    if ($(".selected").hasClass("tree-title")) {
        var folder_name = $(".selected").text();
        if (confirm("Are you sure you want to remove " + folder_name + "? This will remove all sub-directories and sub-routines.")) {
            Sijax.request("remove_folder", [path]);
            $(".selected").parent().empty();
            $(".selected").parent().remove();
            $("#status").append("Folder '" + folder_name + "' removed successfully<br/>");
        }
    } else if ($(".selected").hasClass("tree-item") || $(".selected").hasClass("main-item")) {
        var file_name = $(".selected").text();
        if (confirm("Are you sure you want to remove " + file_name + "?")) {
            var is_routine = $(".selected").hasClass("routine");
            Sijax.request("remove_file", [file_name, is_routine]);
            $(".selected").remove();
            $("#status").append("'" + file_name + "' removed successfully<br/>");
            $("#remove, #unselect").addClass("inactive");
            reset_routine_info();
        }
    }
});

// alternate a folder between open and closed
function setStatus(node){
    var elements = [];
    $(node).each(function(){
        elements.push($(node).nextAll());
    });
    var i;
    for (i = 0; i < elements.length; i++) {
        if (elements[i].css("display") == "none"){
            elements[i].fadeIn(0);
        }else{
            elements[i].fadeOut(0);
        }
    }
    if (elements[0].css("display") != "none") {
        $(node).addClass("active");
    } else {
        $(node).removeClass("active");
    }
}

// get the path associated with the currently selected item
function get_selected_path() {
    return $(".selected").length > 0 ? $(".selected").data("path") : "";
}

// add a file
function add_file(path, filename, routine) {
    var file_element = document.createElement("LI");
    var file_text = document.createTextNode(filename);
    file_element.appendChild(file_text);
    var file_path = path;
    file_element.dataset.path = file_path;
    if (path == "") {
        file_element.className = routine ? "main-item routine": "main-item support";
        document.getElementsByClassName("filetree")[0].appendChild(file_element);
    } else {
        file_element.className = routine ? "tree-item routine": "tree-item support";
        document.getElementsByClassName("selected")[0].parentElement.appendChild(file_element);
        if (!$(".selected").hasClass("active")) {
            setStatus($(".selected"));
        }
    }
}
