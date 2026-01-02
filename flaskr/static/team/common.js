    function afterSubmit() {
        //Qui passo il contenuto della jsgrid (people)
        var data = $("#jsGridPeople").jsGrid("option", "data");
        var dataJSONStringa = JSON.stringify(data);
        document.getElementById('dati_jsGridPeople_json').value = dataJSONStringa;
      
        //Similmente per la jsgrid dei mezzi 
        var data = $("#jsGridTool").jsGrid("option", "data");
        var dataJSONStringa = JSON.stringify(data);
        document.getElementById('dati_jsGridTool_json').value = dataJSONStringa;

        //Similmente per la jsgrid delle attività
        var data = $("#jsGridAct").jsGrid("option", "data");
        var dataJSONStringa = JSON.stringify(data);
        document.getElementById('dati_jsGridAct_json').value = dataJSONStringa;
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

       