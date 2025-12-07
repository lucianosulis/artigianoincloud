  function afterSubmitCreate() {
    
    var tool_ids = $("#tool_ids").val() || []
    document.getElementById("input_tool_ids").value = tool_ids.join();
    var data = $("#jsGrid").jsGrid("option", "data");
    //console.log(data);
    var order_ids_sel = "";
    var ore_lavs_sel = "";

    for (let i = 0; i < data.length; i++) {
      tu_record = data[i];
  
      if (order_ids_sel != "") {
        order_ids_sel = order_ids_sel + ",";
      }
      order_ids_sel = order_ids_sel + ts_record["order_id"];
      document.getElementById("order_ids_sel").value = order_ids_sel;

      if (ore_lavs_sel != "") {
        ore_lavs_sel = ore_lavs_sel + ",";
      }
      ore_lavs_sel = ore_lavs_sel + ts_record["ore_lav"];
      document.getElementById("ore_lavs_sel").value = ore_lavs_sel;

    }
  }

  function afterSubmitCreate2() {
    var tool_ids = $("#tool_ids").val() || []
    document.getElementById("input_tool_ids").value = tool_ids.join();
  }
  
  function afterSubmitUpdate() {
    var new_order_id = document.getElementById("order_id").value;
    var new_tool_id = document.getElementById("tool_id").value;
    document.getElementById("input_tool_id").value = new_tool_id;
    document.getElementById("input_order_id").value = new_order_id;
  }
  function setComboOrders() {
      var date = document.getElementById("date").value
      let selectBox = document.getElementById("order_id");
      function removeAll(select) {
                while (select.options.length > 0) {
                  select.remove(0);
                  }
                }
      removeAll(selectBox);
      selectBox.required = false;
  }

    function setComboOrders2() {
            var date = document.getElementById("date").value
            $.ajax({
            type: "POST",
            url: "/tu_sel_order2" + "/" + date,
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
              document.getElementById("order_ids").value = result['order_id'];
              document.getElementById("order_descs").value = result['order_desc'];
              load_grid();
            } 
          }); 
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
    var tu_records = [];
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
        data: tu_records,
            
        fields: [
            { name: "order_id", title: "Ordine", type: "select", items: orderList, valueField: "order_id", textField: "order_desc", width: "50%", align: "left", validate: { message: "E'obbligatorio specificare l'ordine.", validator: function(value) {if (value != "") {return true} else {return false}}}},
            { name: "ore_lav", title: "Ore", type: "decimalnumber", readOnly: false,  width: "20%", align: "right"},
            { type: "control" }
        ]
      });
  }



