var sample_recipe = "간장 계란밥(2인분)\n" +
    "[기본 재료]\n" +
    "달걀 2개\n" +
    "밥 2공기\n" +
    "김가루 적당량\n" +
    "간장 1큰술\n" +
    "버터 2큰술\n" +
    "통깨 약간\n" +
    "쪽파 (대파로 대체 또는 생략 가능) 2줄기\n" +
    "참기름(또는 들기름) 1큰술 \n" +
    "[조리방법]\n" +
    "1. 달군 팬에 버터를 두른 후 달걀프라이를 겉면이 타듯이 노릇하게 구워주세요.\n" +
    "2. 쪽파는 송송 썰어주세요.\n" +
    "3. 그릇에 따뜻한 밥을 담은 후 달걀프라이를 얹어주세요.\n" +
    "4. 간장과 참기름을 둘러주고 통깨와 쪽파, 김가루를 뿌려 완성해주세요.\n"

$(document).ready(function(){
  $("#recipe-box").val(sample_recipe);
});

$(document).on('submit', '#insert-recipe', function() {
  var $this = $(this);

  $.post($this.attr('action'), $this.serialize())
    .done(function(data) {
      $("#memDiv").empty();
      var sequence_list = JSON.parse(data);
      for (var i = 0; i < sequence_list.length; i++) {
        var sequence = sequence_list[i];
        var insertTr = "";
        insertTr += "<tr>";
        insertTr += "<td>" + sequence['sentence'] + "</td>";
        insertTr += "<td>" + sequence['zone'] + "</td>";
        insertTr += "<td>" + sequence['tool'].join(",") + "</td>";
        insertTr += "<td>";
        for (var j = 0; j < sequence['ingre'].length; j++) {
          insertTr += sequence['ingre'][j];
          if (sequence['volume'].length > j) {
            insertTr += "(" + sequence['volume'][j] + ")";
          }
        }
        insertTr += "</td>";
        insertTr += "<td>" + sequence['seasoning'].join(",") + "</td>";
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
      alert(xhr.responseText);
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