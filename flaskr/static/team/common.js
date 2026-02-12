    function afterSubmit() {
      //Qui passo il contenuto della jsgrid delle attività
        var data = $("#jsGridAct").jsGrid("option", "data");
        var dataJSONStringa = JSON.stringify(data);
        document.getElementById('dati_jsGridAct_json').value = dataJSONStringa;  
      
      //Qui passo il contenuto della jsgrid (people)
        var data = $("#jsGridPeople").jsGrid("option", "data");
        var dataJSONStringa = JSON.stringify(data);
        document.getElementById('dati_jsGridPeople_json').value = dataJSONStringa;
      
      //Similmente per la jsgrid dei mezzi 
      var data = $("#jsGridTool").jsGrid("option", "data");
      const tuttiValidi = data.every(item => item.hasOwnProperty('tool_id'));
      if (!tuttiValidi) {
          console.log("Errore: Uno o più elementi non hanno il tool_id");
          alert("Devi completare i mezzi.")
          return false;
      }
      var dataJSONStringa = JSON.stringify(data);
      console.log("jsGridTool:");
      console.log(dataJSONStringa);
      document.getElementById('dati_jsGridTool_json').value = dataJSONStringa;
      return true;
  }

  function setTeamAct() {
            var date = document.getElementById("date").value
            $.ajax({
            type: "POST",
            url: "/team_sel_acts" + "/" + date,
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
    
              console.log("result:");
              console.log(result);
              load_gridAct(result);
            } 
          }); 
      }

function load_gridAct(result) {
    var team_act = [];
    var anag_act = result;
        
    $("#jsGridAct").jsGrid({
                    width: "40%",
                    height: "400px",
                    inserting: true, 
                    editing: true,
                    sorting: true,
                    paging: true,
                    data: team_act,
                        
                    fields: [
                        { name: "act_id", title: "Attività", type: "select", items: anag_act, valueField: "act_id", textField: "act_desc", width: "50%", align: "left" }, 
                        { type: "control" }
                    ]
                  });
}

//Precompilazione tool_type dai tag
    $("#btn-put_tool_type").click(function() {
            //lettura degli act_id dalla griglia 
            const dataAct = $("#jsGridAct").jsGrid("option", "data");
            const actIds = dataAct.map(item => item.act_id);
            console.log(actIds); 
            $.ajax({
                type: "POST",
                url: "/team_sel_tool_type",
                contentType: "application/json",
                dataType: 'json',
                data: JSON.stringify({ ids: actIds }),
                success: function(result) {
                tool_types = result;
                console.log("Arrivano i dati:")
                console.log(tool_types)
                load_grid_tools(tool_types)
                }  
            }); 
          
        });

function load_grid_tools(tools) {
    // Variabili per memorizzare i riferimenti ai controlli correnti
    var $insertMezzoSelect;
    var $editMezzoSelect;

    $("#jsGridTool").jsGrid({
        width: "40%",
        inserting: true,
        editing: true,
        data: tools,
        fields: [
            {
                name: "type_id",
                title: "Categoria",
                type: "select",
                items: anag_tool_type,
                valueField: "type_id",
                textField: "type",
                width: "50%", align: "left",
                insertTemplate: function() {
                    // 1. Creiamo la select della categoria usando il metodo standard
                    var $select = jsGrid.fields.select.prototype.insertTemplate.call(this);
                    
                    // 2. Al cambio categoria, popoliamo la select dei mezzi
                    $select.on("change", function() {
                        var catId = parseInt($(this).val());
                        updateDropdown($insertMezzoSelect, catId);
                    });

                    // Inizializzazione: aspetta che la riga sia pronta e popola
                    setTimeout(function() { $select.trigger("change"); }, 10);
                    return $select;
                },
                editTemplate: function(value) {
                    var $select = jsGrid.fields.select.prototype.editTemplate.call(this, value);
                    $select.on("change", function() {
                        var catId = parseInt($(this).val());
                        updateDropdown($editMezzoSelect, catId);
                    });
                    return $select;
                }
            },
            {
                name: "tool_id", // ID del Mezzo
                title: "Mezzo",
                type: "select", // Manteniamo select per la visualizzazione in tabella
                items: anag_tools,
                valueField: "tool_id",
                textField: "name",
                width: "50%", align: "left",
                insertTemplate: function() {
                    // Creiamo manualmente la select per avere il controllo totale
                    $insertMezzoSelect = $("<select>").addClass("jsgrid-insert-control");
                    return $insertMezzoSelect;
                },
                editTemplate: function(value, item) {
                    // Creiamo manualmente la select per la modifica
                    $editMezzoSelect = $("<select>").addClass("jsgrid-edit-control");
                    updateDropdown($editMezzoSelect, item.type_id);
                    $editMezzoSelect.val(value);
                    return $editMezzoSelect;
                },
                insertValue: function() {
                    return parseInt($insertMezzoSelect.val());
                },
                editValue: function() {
                    return parseInt($editMezzoSelect.val());
                }
            },
            { type: "control" }
        ]
    });
}

// Funzione centralizzata per popolare qualsiasi select (insert o edit)
function updateDropdown($selectControl, categoryId) {
    if (!$selectControl) return;

    $selectControl.empty();
    
    var filtered = anag_tools.filter(function(item) {
        return item.type_id === categoryId;
    });

    if (filtered.length === 0) {
        $selectControl.append($("<option>").val("").text("Nessun mezzo"));
    } else {
        $.each(filtered, function(index, item) {
            $selectControl.append($("<option>").val(item.tool_id).text(item.name));
        });
    }
}


       