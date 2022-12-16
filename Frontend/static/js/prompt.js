function initPrompt(data) {
  var pre_process = [];
  var fire = [];
  var p_dur = Array();
  var f_dur = Array();
  var dur = Array();
  var zone_list = Array();
  var p_total = 0;
  var f_total = 0;


  if (data === undefined){
    $('#info').html('<p>An error has occurred</p>');
  }

  $("#memDiv1").empty();
  $("#memDiv2").empty();
  const length = Object.keys(data).length;

  var f_pre_duration = 0;
  var f_duration = 0;
  var p_pre_duration = 0;
  var p_duration = 0;
  var found = "";
  var result = "";
  var p_total = 0;
  var f_total = 0;


  for (var i = 0; i < length; i++) {

    var zone = data[i].zone;
    var tools = data[i].tool;
    var ingredient = data[i].ingre;
    var seasoning = data[i].seasoning;
    var volume = data[i].volume;
    var act = data[i].act;

    var insertTr = "";
    insertTr += "<tr>";


    if (zone == "전처리존") {
      if (data[i].duration == "") {
        p_pre_duration = p_duration;
        p_duration = p_duration + 2;
        //insertTr += "<td>" + "</td>";
      } else {
        p_pre_duration = p_duration;
        var str = data[i].duration.replace(/[0-9]/g, "");
        str = str.replace(/[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]/g, "");
        found = data[i].duration.match(/\d+/g);
        var ti = 0;
        if (str == '초') {
          ti = 1;
        } else if (str == '분') {
          ti = 60;
        } else {
          ti = 3600;
        }
        if (found.length == 1) {
          p_duration = p_duration + parseInt(found) * ti;
        } else {
          result = (parseInt(found[0]) + parseInt(found[1])) / 2;
          p_duration = p_duration + result * ti;
        }
        /*
        var p_time = p_duration-p_pre_duration;
        if(p_time<60){
            insertTr += "<td>" + p_time + "초" + "</td>";
        }
        else{
          insertTr += "<td>" + p_time/60 + "분" + "</td>";
        }*/
      }

      var insertTr = "";
      insertTr += "<tr>";
      var p_time = p_duration-p_pre_duration;
      if(p_time<60){
          insertTr += "<td>" + p_time + "초" + "</td>";
      }
      else{
        insertTr += "<td>" + p_time/60 + "분" + "</td>";
      }


      insertTr += "<td>" + tools.join(", ") + "</td>";
      insertTr += "<td>";
      for (var j = 0; j < ingredient.length; j++) {
        insertTr += ingredient[j];
        if (volume.length > j) {
          insertTr += "(" + volume[j] + ")";
        }
        if (j !== ingredient.length - 1) {
          insertTr += "<br>"
        }
      }
      insertTr += "</td>";
      insertTr += "<td>" + seasoning.join("<br>") + "</td>";
      insertTr += "<td>" + act + "</td>";
      insertTr += "</tr>";

      $("#memDiv1").append(insertTr);
      zone_list.push('p');
      p_dur.push(p_duration - p_pre_duration);


  } else if (zone == "화구존") {
    if (data[i].duration == "") {
      f_pre_duration = f_duration;
      f_duration = f_duration + 2;
    } else {
      f_pre_duration = f_duration;
      var str = data[i].duration.replace(/[0-9]/g, "");
      str = str.replace(/[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]/g, "");
      found = data[i].duration.match(/\d+/g);
      var ti = 0;
      if (str == '초') {
        ti = 1;
      } else if (str == '분') {
        ti = 60;
      } else {
        ti = 3600;
      }
      if (found.length == 1) {
        f_duration = f_duration + parseInt(found) * ti;
      } else {
        result = (parseInt(found[0]) + parseInt(found[1])) / 2;
        f_duration = f_duration + result * ti;
      }
    }
    var f_time = f_duration-f_pre_duration;
    var insertTr = "";
    insertTr += "<tr>";
    if(f_time<60){
        insertTr += "<td>" + f_time + "초" + "</td>";
    }
    else{
      insertTr += "<td>" + f_time/60 + "분" + "</td>";
    }
    insertTr += "<td>" + tools.join(", ") + "</td>";
    insertTr += "<td>";
    for (var j = 0; j < ingredient.length; j++) {
      insertTr += ingredient[j];
      if (volume.length > j) {
        insertTr += "(" + volume[j] + ")";
      }
      if (j !== ingredient.length - 1) {
        insertTr += "<br>"
      }
    }
    insertTr += "</td>";
    insertTr += "<td>" + seasoning.join("<br>") + "</td>";
    insertTr += "<td>" + act + "</td>";
    insertTr += "</tr>";

    $("#memDiv2").append(insertTr);
    zone_list.push('f');
    f_dur.push(f_duration - f_pre_duration);
  }

}


    function show_time() {

      var total_time = f_dur.reduce(function add(sum, currValue) {
        return sum + currValue;
      }, 0);

      p_total = p_dur.reduce(function add(sum, currValue) {
        return sum + currValue;
      }, 0);

      f_total = total_time;

      var fp_total = f_total + p_total;

      var hour = parseInt(fp_total / 3600);
      var min = parseInt((fp_total % 3600) / 60);
      var sec = fp_total % 60;

      if (hour == 0 && min == 0) {
        $('#total_ti').text('총 예상 시간: ' + sec + '초');
      } else if (hour == 0 && sec == 0) {
        $('#total_ti').text('총 예상 시간: ' + min + '분');
      } else if (min == 0 && sec == 0) {
        $('#total_ti').text('총 예상 시간: ' + hour + '시간');
      } else if (hour == 0) {
        $('#total_ti').text('총 예상 시간: ' + min + '분 ' + sec + '초');
      } else if (min == 0) {
        $('#total_ti').text('총 예상 시간: ' + hour + '시간 ' + sec + '초');
      } else if (sec == 0) {
        $('#total_ti').text('총 예상 시간: ' + hour + '시간 ' + min + '분');
      } else {
        $('#total_ti').text('총 예상 시간: ' + hour + '시간 ' + min + '분 ' + sec + '초');
      }
    }

    show_time();

    var tot_pr1 = 0;
    var tot_pr2 = 0;

    function moveBtn1(duration) {
      tot_pr1 += duration;
      var id = setInterval(frame, 45);

      function frame() {
        if (tot_pr1 > 100) {
          clearInterval(id);
        } else {
          $('#progressing_p').css("width", Math.ceil(tot_pr1) + "%");
          $('#progressing_p').text(Math.ceil(tot_pr1) + "%");
        }
      }
    }

    function moveBtn2(duration) {
      tot_pr2 += duration;
      var id = setInterval(frame, 45);

      function frame() {
        if (tot_pr2 > 100) {
          clearInterval(id);
        } else {
          $('#progressing_f').css("width", Math.ceil(tot_pr2) + "%");
          $('#progressing_f').text(Math.ceil(tot_pr2) + "%");
        }
      }
    }


    var count = 0;
    var current_time = 0;
    var prog_bar = 0;

    var p_index = 1,
      f_index = 1;

    function setIntervalFunc(duration) {
      moveBtn1(duration / p_total * 100);
      $('#preprocessing_table > tbody > tr:nth-child(' + p_index + ')').children().css("background-color", "#00FF7F");
      $('#preprocessing_table > tbody > tr:nth-child(' + p_index + ')').children().css("color", "black");
      $('#preprocessing_table > tbody > tr:nth-child(' + p_index + ')').children().css("font-weight", "bold");
      setTimeout(function(index) {
        $('#preprocessing_table > tbody > tr:nth-child(' + index + ')').children().css("background-color", "black");
        $('#preprocessing_table > tbody > tr:nth-child(' + index + ')').children().css("color", "grey");
        $('#preprocessing_table > tbody > tr:nth-child(' + index + ')').children().css("font-weight", "normal");

      }, duration * 1000, p_index);
      current_time = current_time + duration;
      p_index++;
    }

    function setIntervalFunc_2(duration){
      moveBtn2(duration/f_total*100);
      $('#fire_table > tbody > tr:nth-child(' + f_index + ')').children().css("background-color", "#80ffff");
      $('#fire_table > tbody > tr:nth-child(' + f_index + ')').children().css("color", "black");
      $('#fire_table > tbody > tr:nth-child(' + f_index + ')').children().css("font-weight", "bold");
      setTimeout(function(index) {
        $('#fire_table > tbody > tr:nth-child(' + index + ')').children().css("background-color", "black");
        $('#fire_table > tbody > tr:nth-child(' + index + ')').children().css("color", "grey");
        $('#fire_table > tbody > tr:nth-child(' + index + ')').children().css("font-weight", "normal");
        //console.log(index);
      }, duration * 1000, f_index);
      current_time = current_time + duration;
      f_index++;
    }

    var ms = 0;
    for (var i = 0; i < p_dur.length; i++) {
      if (i !== 0) {
        ms += p_dur[i - 1];
      }
      setTimeout(function(duration) {
        setIntervalFunc(duration);
      }, ms * 1000, p_dur[i]);
    }

    ms = 0;
    for (var i = 0; i < f_dur.length; i++) {
      if (i !== 0) {
        ms += f_dur[i - 1];
      }
      setTimeout(function(duration) {
        setIntervalFunc_2(duration);
      }, ms * 1000, f_dur[i]);
    }
}