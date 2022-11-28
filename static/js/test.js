const element = document.getElementById("btn_create");
element.addEventListener("click", sendData);

const element2 = document.getElementById("refresh-btn");
element2.addEventListener("click", refresh);

async function sendData() {
  $("#memDiv tr").remove(); 
  let setload = document.getElementById("loadcontent")
  setload.style.display = "block"

  let text = document.getElementById("recipe-box").value
  let jsonform = text.replace("\n", "\\n")
  //console.log(jsonform)
  let data = {
    "name": "Flask Room",
    "description": jsonform,
  }
  //console.log(data)
  let response = await fetch("/returnjson",{
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": JSON.stringify(data),
  })
  let sequence_list = await response.json();
  //.then(response => console.log(response.json()))
  //var sequence_list = await response.json();
  for (var i = 0; i < sequence_list["hi"].length; i++) 
  {
    var sequence = sequence_list["hi"][i];
    console.log(sequence)
    var insertTr = "";
        insertTr += "<tr>";
        insertTr += "<td>" + sequence['sentence'] + "</td>";
        insertTr += "<td>" + sequence['zone'] + "</td>";
        insertTr += "<td>" + sequence['tool'] + "</td>";
        insertTr += "<td>" + sequence['act'] + "</td>";
        $("#memDiv").append(insertTr);
  }
  setload.style.display = "none"
  console.log("done")
};

async function refresh() {
  $("#memDiv tr").remove(); 
  let response = await fetch("/refresh",{
    "method": "GET",
  })
  let newtext = await response.json();
  $("#recipe-box").val(newtext["refresh"]);
};