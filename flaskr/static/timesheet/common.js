  function afterSubmitCreate() {
    const data = $("#jsGrid").jsGrid("option", "data");
    const dataJSONStringa = JSON.stringify(data);
    document.getElementById('dati_griglia_json').value = dataJSONStringa;
    const data1 = $("#jsGrid1").jsGrid("option", "data");
    const dataJSONStringa1 = JSON.stringify(data1);
    document.getElementById('dati_griglia_json1').value = dataJSONStringa1;
  } 

  function afterSubmitCreate2() {
    var people_ids = $("#people_ids").val() || []
    document.getElementById("input_people_ids").value = people_ids.join();
  }
  
  function afterSubmitUpdate() {
    if (document.getElementById("night").checked == true) {
      document.getElementById("night").value = 1;
    }
    else {
      document.getElementById("night").value = 0;
    }
  }
  
  function setComboActs() {
      console.log(setComboActs);
      var act_type_id = document.getElementById("act_type_id").value
      var date = document.getElementById("date").value
      let selectBox = document.getElementById("act_id");
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
            url: "/ts_sel_act" + "/" + date,
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
          }); 
      }
  }

  function setComboActs2() {
            var date = document.getElementById("date").value
            $.ajax({
            type: "POST",
            url: "/ts_sel_act2" + "/" + date,
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
              acts = result
              load_grid(act_types,acts);
            }  
          }); 
          $.ajax({
            type: "POST",
            url: "/tu_sel_act2" + "/" + date,
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
              acts = result;
              load_grid1(anag_tools1,acts);
            }  
          }); 
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

  function load_grid(act_types,acts) {
    var ts_records = [];
        
    $("#jsGrid").jsGrid({
        width: "100%",
        height: "400px",
        inserting: true,
        editing: true,
        sorting: true,
        paging: true,
        data: ts_records,
            
        fields: [
            { name: "act_type_id", title: "Tipo attività", type: "select", items: act_types, valueField: "act_type_id", textField: "act_type_desc", width: "30%", align: "left" },
            { name: "act_id", title: "Attività", type: "select", items: acts, valueField: "act_id", textField: "act_desc", width: "50%", align: "left", validate: { message: "Se è un cantiere è obbligatorio specificare l'attività; negli altri casi l'attività dev'essere vuota.", validator: function(value, item) {if ((item.act_type_id == 1 && value != "") || (item.act_type_id != 1 && value == "")) {return true} else {return false}}}},
            { name: "ore_lav", title: "Ore", type: "decimalnumber", readOnly: false,  width: "20%", align: "right"},
            { name: "night", title: "Notturno", type: "checkbox"},
            { type: "control" }
        ]
      });
  }

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


