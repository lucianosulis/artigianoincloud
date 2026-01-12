  function afterSubmitCreate() {
    const data1 = $("#jsGrid1").jsGrid("option", "data");
    const dataJSONStringa1 = JSON.stringify(data1);
    document.getElementById('dati_griglia_json1').value = dataJSONStringa1;
    const data2 = $("#jsGrid2").jsGrid("option", "data");
    const dataJSONStringa2 = JSON.stringify(data2);
    document.getElementById('dati_griglia_json2').value = dataJSONStringa2;
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
  
  function setComboActs() {
      console.log(setComboActs);
      var date = document.getElementById("date").value
      let selectBox = document.getElementById("act_id");
      function removeAll(select) {
                while (select.options.length > 0) {
                  select.remove(0);
                  }
                }
      removeAll(selectBox);
      selectBox.required = false;
      $.ajax({
      type: "POST",
      url: "/tu_sel_act" + "/" + date,
      contentType: "application/json",
      dataType: 'json',
      success: function(result) {
        selectBox.required = true;
        const option0 = new Option("Selezionare un'attività","");
        option0.setAttribute("disabled","disabled");
        option0.setAttribute("selected",true);
        selectBox.add(option0, undefined);
        for (let i = 0; i < result.length; i++) {
          const option = new Option(result[i]['act_desc'],result[i]['act_id']);
          selectBox.add(option, undefined);
        }
      }
      })
  }; 

  function setComboActs2() {
            var date = document.getElementById("date").value
            $.ajax({
            type: "POST",
            url: "/tu_sel_act2" + "/" + date,
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
              acts = result;
              load_grid1(anag_tools1,acts);
              load_grid2(anag_tools2,acts);
            }  
          }); 
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

  function load_grid1(anag_tools1,acts) {
    var tu_records = [];
    
    $("#jsGrid1").jsGrid({
        width: "100%",
        height: "300px",
        inserting: true,
        editing: true,
        sorting: true, 
        paging: true,
        data: tu_records,
            
        fields: [
            { name: "act_id", title: "Attività", type: "select", items: acts, valueField: "act_id", textField: "act_desc", width: "50%", align: "left", validate: { message: "E'obbligatorio specificare l'attività.", validator: function(value) {if (value != "") {return true} else {return false}}}},
            { name: "tool_id", title: "Mezzo", type: "select", items: anag_tools1, valueField: "tool_id", textField: "tool_name", width: "50%", align: "left", validate: { message: "E'obbligatorio specificare il mezzo.", validator: function(value) {if (value != "") {return true} else {return false}}}},
            { name: "ore_lav", title: "Ore", type: "decimalnumber", readOnly: false,  width: "20%", align: "right"},
            { type: "control" }
        ]
      });
  }

  function load_grid2(anag_tools2,acts) {
    var tu_records = [];
    
    $("#jsGrid2").jsGrid({
        width: "100%",
        height: "300px",
        inserting: true,
        editing: true,
        sorting: true, 
        paging: true,
        data: tu_records,
            
        fields: [
            { name: "act_id", title: "Attività", type: "select", items: acts, valueField: "act_id", textField: "act_desc", width: "50%", align: "left", validate: { message: "E'obbligatorio specificare l'attività.", validator: function(value) {if (value != "") {return true} else {return false}}}},
            { name: "tool_id", title: "Mezzo", type: "select", items: anag_tools2, valueField: "tool_id", textField: "tool_name", width: "50%", align: "left", validate: { message: "E'obbligatorio specificare il mezzo.", validator: function(value) {if (value != "") {return true} else {return false}}}},
            { name: "km", title: "Km", type: "decimalnumber", readOnly: false,  width: "20%", align: "right"},
            { type: "control" }
        ]
      });
  }

  function load_grid3(anag_tools2,acts) {
    var tu_records = [];
    
    $("#jsGrid3").jsGrid({
        width: "100%",
        height: "300px",
        inserting: true,
        editing: true,
        sorting: true, 
        paging: true,
        data: tu_records,
            
        fields: [
            { name: "act_id", title: "Attività", type: "select", items: acts, valueField: "act_id", textField: "act_desc", width: "50%", align: "left", validate: { message: "E'obbligatorio specificare l'attività.", validator: function(value) {if (value != "") {return true} else {return false}}}},
            { name: "tool_id", title: "Mezzo", type: "select", items: anag_tools2, valueField: "tool_id", textField: "tool_name", width: "50%", align: "left", validate: { message: "E'obbligatorio specificare il mezzo.", validator: function(value) {if (value != "") {return true} else {return false}}}},
            { name: "km", title: "Km", type: "decimalnumber", readOnly: false,  width: "20%", align: "right"},
            { type: "control" }
        ]
      });
  }


