  function afterSubmit() {
    try{ 
    const data = $("#jsGrid").jsGrid("option", "data");
    const dataJSONStringa = JSON.stringify(data);
    document.getElementById('dati_griglia_json').value = dataJSONStringa;
    }
    catch(err) {alert(err.message)}
  }
function afterSubmitUpdate() { 
    var new_order_id = document.getElementById("order_id").value;
    var new_act_type_id = document.getElementById("act_type_id").value;
    document.getElementById("input_act_type_id").value = new_act_type_id;
    document.getElementById("input_order_id").value = new_order_id;
    if (document.getElementById("night").checked == true) {
      document.getElementById("input_night").value = 1;
    }
    else {
      document.getElementById("input_night").value = 0;
    }
  }
    function setComboOrders() {
      var act_type_id = document.getElementById("act_type_id").value
      var date = document.getElementById("date").value
      let selectBox = document.getElementById("order_id");
      function removeAll(select) {
                while (select.options.length > 0) {
                  select.remove(0);
                  }
                }
      removeAll(selectBox);
      selectBox.required = false;
      if (act_type_id == 1) { 
            $.ajax({
            type: "POST",
            url: "/ts_sel_order" + "/" + date,
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
              selectBox.required = true;
              const option0 = new Option("Selezionare un ordine","");
              option0.setAttribute("disabled","disabled");
              option0.setAttribute("selected",true);
              selectBox.add(option0, undefined);
              for (let i = 0; i < result.length; i++) {
                const option = new Option(result[i]['full_name'] + ' - ' + result[i]['description'],result[i]['id']);
                selectBox.add(option, undefined);
              }
            } 
          }); 
      }
    }

    function setComboOrders2() {
            var date = document.getElementById("date").value
            $.ajax({
            type: "POST",
            url: "/ts_sel_order2" + "/" + date,
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
              document.getElementById("order_ids").value = result['order_id'];
              document.getElementById("order_descs").value = result['order_desc'];
              load_grid();
            } 
          }); 
      }
      
    function setComboOrdersFilter(act_type_id_Object) {
      var act_type_id = act_type_id_Object.value;
      let selectBox = document.getElementById("order_id");
      function removeAll(select) {
                while (select.options.length > 0) {
                  select.remove(0);
                  }
                }
      removeAll(selectBox);
      selectBox.required = false;
      if (act_type_id == 1) { 
            $.ajax({
            type: "POST",
            url: "/ts_sel_order",
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
              selectBox.required = true;
              const option0 = new Option("Selezionare un ordine","");
              option0.setAttribute("disabled","disabled");
              option0.setAttribute("selected",true);
              selectBox.add(option0, undefined);
              for (let i = 0; i < result.length; i++) {
                const option = new Option(result[i][2] + ' - ' + result[i][1],result[i][0]);
                selectBox.add(option, undefined);
              }
            } 
          }); 
      }
    }

function FloatNumberField(config) {
      jsGrid.NumberField.call(this, config);
  }
  FloatNumberField.prototype = new jsGrid.NumberField({
    insertValue: function() {
      if (this.insertControl.val() == null || this.insertControl.val() == "") {
      return 0;
      }
      else { return parseFloat(this.insertControl.val());}
  },
  editValue: function() {
      return parseFloat(this.editControl.val());
  }
  });
  jsGrid.fields.decimalnumber = FloatNumberField;

  function load_grid() {
    var ts_records = [];

    var act_type_ids = document.getElementById("act_type_ids").value;
    //console.log("act_type_ids: " + act_type_ids);
    var act_type_ids_arr = act_type_ids.split(",");
    var act_type_descs = document.getElementById("act_type_descs").value;
    //console.log(act_type_descs);
    var act_type_descs_arr = act_type_descs.split(",");
    //console.log(act_type_ids_arr);

    var act_type_list = [];
    for (let i = 0; i < act_type_ids_arr.length; i++) {
      var new_element = '{"act_type_id": ' + act_type_ids_arr[i] + ', "act_type_desc": "' + act_type_descs_arr[i] + '"}';
      //console.log(new_element);
      var new_object = JSON.parse(new_element);
      act_type_list.push(new_object);
    }
    var orderList = [];
    var order_ids = document.getElementById("order_ids").value;
    var order_ids_arr = order_ids.split(",");
    var order_descs = document.getElementById("order_descs").value;
    var order_descs_arr = order_descs.split("|§|");
    for (let i = 0; i < order_ids_arr.length; i++) {
      var new_element = '{"order_id": "' + order_ids_arr[i] + '", "order_desc": "' + order_descs_arr[i] + '"}';
      var new_object = JSON.parse(new_element);
      orderList.push(new_object);
    }
    
    $("#jsGrid").jsGrid({
        width: "100%",
        height: "400px",
        inserting: true,
        editing: true,
        sorting: true,
        paging: true,
        data: ts_records,
            
        fields: [
            { name: "act_type_id", title: "Tipo attività", type: "select", items: act_type_list, valueField: "act_type_id", textField: "act_type_desc", width: "30%", align: "left" },
            { name: "order_id", title: "Ordine", type: "select", items: orderList, valueField: "order_id", textField: "order_desc", width: "50%", align: "left", validate: { message: "Se è un cantiere è obbligatorio specificare l'ordine; negli altri casi l'ordine dev'essere vuoto.", validator: function(value, item) {if ((item.act_type_id == 1 && value != "") || (item.act_type_id != 1 && value == "")) {return true} else {return false}}}},
            { name: "ore_lav", title: "Ore", type: "decimalnumber", readOnly: false,  width: "20%", align: "right"},
            { name: "night", title: "Notturno", type: "checkbox"},
            { type: "control" }
        ]
      });
  }