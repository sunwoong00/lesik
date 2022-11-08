$(document).on('click', "#refresh-btn", function(){
    $.get("/refresh")
    .done(function(data) {
        $("#recipe-box").val(data);
    })
    .fail(function(xhr, status, error) {
      alert(xhr.responseText);
    });

  return false;
});

$(document).on('click', "#manual", function(){
    window.open("static/templates/manual.html", "a", "width=800, height=800, left=100, top=50");
});

$(document).on('submit', '#insert-recipe', function() {
  var $this = $(this);

  $.post($this.attr('action'), $this.serialize())
    .done(function(data) {
        $("#prompt-recipe_json").val(data);
      $("#memDiv").empty();
      var sequence_list = JSON.parse(data);
      for (var i = 0; i < sequence_list.length; i++) {
        var sequence = sequence_list[i];
        var insertTr = "";
        insertTr += "<tr>";
        insertTr += "<td>" + sequence['sentence'] + "</td>";
        insertTr += "<td>" + sequence['zone'] + "</td>";
        insertTr += "<td>" + sequence['tool'].join(",") + "</td>";
        insertTr += "<td>" + sequence['duration'] + "</td>";
        insertTr += "<td>" + sequence['temperature'] + "</td>"; //선웅 수정
        insertTr += "<td>";

        var j = 0;
        /* 식자재 용량 추출 */
        for (; j < sequence['ingre'].length; j++) {
          insertTr += sequence['ingre'][j];
          if (sequence['volume'].length > j) {
            if ( sequence['volume'][j] !== '' ){
              insertTr += "(" + sequence['volume'][j] + ")";
            }
          }
          if(j !== sequence['ingre'].length - 1){
              insertTr += "<br>"
          }
        }
        insertTr += "</td>"; /* finish ingre section*/


        insertTr += "<td>"; /* start seasoning section */
        /*박지연 첨가물 수정 코드*/
        for (; j < (sequence['ingre'].length + sequence['seasoning'].length); j++) {
          insertTr += sequence['seasoning'][j-sequence['ingre'].length];
          if ( (sequence['volume'].length + sequence['ingre'].length) > j) {
            if ( sequence['volume'][j] !== '' ){
              insertTr += "(" + sequence['volume'][j] + ")";
            }
          }
          if(j !== sequence['ingre'].length + sequence['seasoning'].length - 1){
              insertTr += "<br>"
          }
        }
        /*박지연 첨가물 수정 코드*/
        insertTr += "</td>"; /* finish seasoning section */

        /* 서유정 */

        if(sequence['standard'].length !=0){
          insertTr += "<td>" + sequence['standard'] + "</td>";
        }else{
          insertTr += "<td></td>";
        }
        insertTr += "<td>" + sequence['act'] + "</td>";
        insertTr += "<td><input type='checkbox' form='save-sentence' name='save_sentence' value='";
        insertTr += JSON.stringify(sequence);
        insertTr += "'></td>";
        insertTr += "</tr>";

        $("#memDiv").append(insertTr);
      }

      if(!$("#save-sentence").length){
          var formDOM = "";
          formDOM += "<div class='empty-block'></div><form id='save-sentence' class='ajax-form' action='/save' method='POST' confirm-msg='해당 문장을 저장하시겠습니까?'>";
          formDOM += "<input type='submit' value='저장'/>";
          formDOM += '</form>';
          $("#save_sentence-box").append(formDOM);
      }
    })
    .fail(function(xhr, status, error) {
        if(status === 406){
            alert(xhr.responseText);
        }else{
            alert("서버 내부 오류가 발생했습니다.");
        }

    });

  return false;
});

$(document).on('submit', "#save-sentence", function() {
  var $this = $(this);
  var save_sentences = [];
  $("input[name=save_sentence]:checked").each(function(){
      save_sentences.push($(this).val());
  });

  var confirm_msg = $this.attr('confirm-msg');
  if(confirm_msg !== undefined || confirm_msg !==''){
      if(!window.confirm(confirm_msg)){
          return false;
      }
  }

  var dataDOM = "<input type='hidden' name='data' value='";
  dataDOM += "[";
  dataDOM += save_sentences.join(",");
  dataDOM += "]";
  dataDOM += "'/>";

  $this.append(dataDOM);
  $.post($this.attr('action'), $this.serialize())
    .done(function(data) {
      alert("저장에 성공했습니다");
      $("input[name=data]").remove();
    })
    .fail(function(xhr, status, error) {
      alert(xhr.responseText);
    });

  return false;
});

$(document).on('submit', "#insert-recipe", function() {
  var checkbox = $("input[name=srl_mode]");
  checkbox.val(checkbox.is(":checked"));
});


/*
$("input:checkbox").on('click', function() {
    // in the handler, 'this' refers to the box clicked on
    var $box = $(this);
    if ($box.is(":checked")) {
      // the name of the box is retrieved using the .attr() method
      // as it is assumed and expected to be immutable
      var group = "input:checkbox[id='" + $box.attr("id") + "']";
      // the checked state of the group/box on the other hand will change
      // and the current value is retrieved using .prop() method
      $(group).prop("checked", false);
      $box.prop("checked", true);
    } else {
      $box.prop("checked", false);
    }
  });
*/
