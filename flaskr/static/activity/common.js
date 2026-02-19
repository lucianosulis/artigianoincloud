
console.log("Sono nello script principale di activity/common.js");
        
//Sono costretto a copiare le due SELECT in campi INPUT perché le prime non vengono passate
    //nella request.form (non capisco perché i campi INPUT sì)
    function afterSubmit() {
      //alert("Inizio Submit")
      var new_site_id = document.getElementById("site_id").value;
      document.getElementById("input_site_id").value = new_site_id;
      //Qui passo il contenuto della jsgrid (le persone) come unica stringa 
      //nel campo nascosto peoples per il passaggio a Python
      var data = $("#jsGrid").jsGrid("option", "data");
      var people_ids_Str = "";
      for (let i = 0; i < data.length; i++) {
        var jsonObject = data[i];
        if (people_ids_Str != "") {
          people_ids_Str = people_ids_Str + ",";
        }
        people_ids_Str = people_ids_Str + jsonObject["id"];
      }
      dates_Str = "";
      for (let i = 0; i < data.length; i++) {
        var jsonObject = data[i];
        if (dates_Str != "") {
          dates_Str = dates_Str + ",";
        }
        dates_Str = dates_Str + jsonObject["date"];
      }
      
      console.log("people_ids_Str: "+people_ids_Str);
      console.log("dates_Str: "+dates_Str);
      document.getElementById("people_ids").value = people_ids_Str;
      document.getElementById("people_dates").value = dates_Str;
      
      //Similmente per la jsgrid dei mezzi 
      var data = $("#jsGrid2").jsGrid("option", "data");
      var tool_ids_Str = "";
      for (let i = 0; i < data.length; i++) {
        var jsonObject = data[i];
        if (tool_ids_Str != "") {
          tool_ids_Str = tool_ids_Str + ",";
        }
        tool_ids_Str = tool_ids_Str + jsonObject["id"];
      }
      console.log("tool_ids_Str: " + tool_ids_Str);
      dates_Str = "";
      for (let i = 0; i < data.length; i++) {
        var jsonObject = data[i];
        if (dates_Str != "") {
          dates_Str = dates_Str + ",";
        }
        dates_Str = dates_Str + jsonObject["date"];
      }
      console.log("dates_Str: " + dates_Str);
      console.log("tool_ids_Str: "+tool_ids_Str);
      console.log("dates_Str: " + dates_Str);
      document.getElementById("tool_ids").value = tool_ids_Str;
      document.getElementById("tool_dates").value = dates_Str;
      
  }
//In questo caso devo anche creare l'ordine in Fatture in Cloud
    function afterSubmit2() {
        var new_site_id = document.getElementById("site_id").value;
        document.getElementById("input_site_id").value = new_site_id;
        //Qui passo appoggio il contenuto della jsgrid (le persone) come unica stringa 
        //nel campo nascosto peoples per il passaggio a Python
        var data = $("#jsGrid").jsGrid("option", "data");
      var people_ids_Str = "";
      for (let i = 0; i < data.length; i++) {
        var jsonObject = data[i];
        if (people_ids_Str != "") {
          people_ids_Str = people_ids_Str + ",";
        }
        people_ids_Str = people_ids_Str + jsonObject["id"];
      }
      dates_Str = "";
      for (let i = 0; i < data.length; i++) {
        var jsonObject = data[i];
        if (dates_Str != "") {
          dates_Str = dates_Str + ",";
        }
        dates_Str = dates_Str + jsonObject["date"];
      }
      
      console.log("people_ids_Str: "+people_ids_Str);
      console.log("dates_Str: "+dates_Str);
      document.getElementById("people_ids").value = people_ids_Str;
      document.getElementById("people_dates").value = dates_Str;

        //Similmente per la jsgrid dei mezzi 
      var data = $("#jsGrid2").jsGrid("option", "data");
      var tool_ids_Str = "";
      for (let i = 0; i < data.length; i++) {
        var jsonObject = data[i];
        if (tool_ids_Str != "") {
          tool_ids_Str = tool_ids_Str + ",";
        }
        tool_ids_Str = tool_ids_Str + jsonObject["id"];
      }
      console.log("tool_ids_Str: " + tool_ids_Str);
      dates_Str = "";
      for (let i = 0; i < data.length; i++) {
        var jsonObject = data[i];
        if (dates_Str != "") {
          dates_Str = dates_Str + ",";
        }
        dates_Str = dates_Str + jsonObject["date"];
      }
      console.log("dates_Str: " + dates_Str);
      console.log("tool_ids_Str: "+tool_ids_Str);
      console.log("dates_Str: " + dates_Str);
      document.getElementById("tool_ids").value = tool_ids_Str;
      document.getElementById("tool_dates").value = dates_Str;
    }

    function getComboSite() {
      //alert("Sono in getComboSite")
      var order_id = document.getElementById("order_id").value;  
      //alert(order_id);
      $.ajax({
      type: "POST",
      url: "/" + order_id + "/sel_site",
      contentType: "application/json",
      dataType: 'json',
      success: function(result) {
        console.log("Result:");
        console.log(result);
        let selectBox = document.getElementById("site_id");
        console.log("Indice: " + selectBox.selectedIndex);
        function removeAll(select) {
          while (select.options.length > 0) {
            select.remove(0);
            }
          }
        removeAll(selectBox);
        console.log("Result length: " + result.length);
        console.log("city: " + result[0]['city']);
        for (let i = 0; i < result.length; i++) {
          const option = new Option(result[i]['city'] + ' - ' + result[i]['address'],result[i]['id']);
          selectBox.add(option, undefined);
        }
      } 
    });
    }
 
    function getComboSite2() {
      var customer_id = document.getElementById("customer_id").value;  
      //alert("Sono in getComboSite2")
      console.log(customer_id);
      $.ajax({
      type: "POST",
      url: "/" + customer_id + "/sel_site2",    
      contentType: "application/json",
      dataType: 'json',
      success: function(result) {
        console.log("Result:");
        console.log(result);
        let selectBox = document.getElementById("site_id");
        console.log("Indice: " + selectBox.selectedIndex);
        function removeAll(select) {
          while (select.options.length > 0) {
            select.remove(0);
            }
          }
        removeAll(selectBox);
        console.log("Result length: " + result.length);
        console.log("city: " + result[0]['city']);
        for (let i = 0; i < result.length; i++) {
          const option = new Option(result[i]['city'] + ' - ' + result[i]['address'],result[i]['id']);
          selectBox.add(option, undefined);
        }
      } 
    });
    }

    function setEndDate() {
      let endDate = document.getElementById("end").value; 
      if (endDate == null || endDate == "") {
        endDate = document.getElementById("start").value;
        document.getElementById("end").value = endDate;
      }
    }

    function getOrderTags(order_id) {  
      //alert(order_id);
      $.ajax({
      type: "POST",
      url: "/" + order_id + "/get_order_tags",
      contentType: "application/json",
      dataType: 'json',
      success: function(result) {
        console.log("Result:");
        console.log(result);
        let selectBox = document.getElementById("tag_id");
        console.log("Indice: " + selectBox.selectedIndex);
        function removeAll(select) {
          while (select.options.length > 0) {
            select.remove(0);
            }
          } 
        removeAll(selectBox);
        for (let i = 0; i < result.length; i++) {
          const option = new Option(result[i]['tag_desc'],result[i]['tag_id']);
          // Imposta come selezionato se è il primo elemento
          if (i === 0) {
            option.selected = true;
          }
          selectBox.add(option, undefined);
        }
      } 
    });
    }

    function open_order_select() {
      window.open(document.getElementById("url").value,"Ordini", "toolbar=no,fullscreen=yes");
      //window.open(document.getElementById("{{ url_for('order.select') }}").value,"Ordini");
      
    }

    function open_customer_select() {
      window.open(document.getElementById("url").value,"Clienti", "toolbar=no,fullscreen=yes");
    }



       