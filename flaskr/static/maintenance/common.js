
console.log("Sono nello script principale di maintenance/common.js");

//Sono costretto a copiare la SELECT in un campo INPUT perché altrimenti non viene passata
//nella request.form (non capisco perché i campi INPUT sì)
    function afterSubmit() {
      var new_tool_id = document.getElementById("tool_id").value;
      document.getElementById("input_tool_id").value = new_tool_id;
  
      if (document.getElementById("radio1").checked == true) {
        document.getElementById("extra").value = "0";
      }
      else {document.getElementById("extra").value = "1";}
  }

    function setEndDate() {
      let endDate = document.getElementById("end").value; 
      if (endDate == null || endDate == "") {
        endDate = document.getElementById("start").value;
        document.getElementById("end").value = endDate;
      }
    }


       