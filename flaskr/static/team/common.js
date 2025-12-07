
console.log("Sono nello script principale di team/common.js");
        var people_ids = document.getElementById("people_ids").value;
        console.log("people_ids: " + people_ids);
        if (people_ids != "" && people_ids != null && people_ids != "None") {
          console.log("sono nella if");
          var people_names = document.getElementById("people_names").value;
            var people_ids_arr = people_ids.split(",");
            var people_names_arr = people_names.split(",");
            var team_people = [];
            for (let i = 0; i < people_ids_arr.length; i++) {
              var new_element = '{"id": ' + people_ids_arr[i] + ',"name": "' + people_names_arr[i] + '"}';
              console.log(new_element);
              var new_object = JSON.parse(new_element);
              team_people.push(new_object);
            }  
            console.log(team_people);
          }
        var tool_ids = document.getElementById("tool_ids").value;
        console.log("tool_ids: " + tool_ids);
        if (tool_ids != "" && tool_ids != null && tool_ids != "None") {
          console.log("sono nella seconda if");
          var tool_names = document.getElementById("tool_names").value;
            var tool_ids_arr = tool_ids.split(",");
            var tool_names_arr = tool_names.split(",");
            var team_tool = [];
            for (let i = 0; i < tool_ids_arr.length; i++) {
              var new_element = '{"id": ' + tool_ids_arr[i] + ',"name": "' + tool_names_arr[i] + '"}';
              console.log(new_element);
              var new_object = JSON.parse(new_element);
              team_tool.push(new_object);
            }  
            console.log(team_tool);
          }
    
          var anag_people_ids = document.getElementById("anag_people_ids").value;
          var anag_people_ids_arr = anag_people_ids.split(",");
          console.log(people_ids_arr);
          var anag_people_names = document.getElementById("anag_people_names").value;
          var anag_people_names_arr = anag_people_names.split(",");
          console.log(people_names_arr);
        
        var anag_people = [];
        for (let i = 0; i < anag_people_ids_arr.length; i++) {
          var new_element = '{"id": ' + anag_people_ids_arr[i] + ', "name": "' + anag_people_names_arr[i] + '"}';
          console.log(new_element);
          var new_object = JSON.parse(new_element);
          anag_people.push(new_object);

        }
        console.log(anag_people);        

        var anag_tool_ids = document.getElementById("anag_tool_ids").value;
          var anag_tool_ids_arr = anag_tool_ids.split(",");
          console.log(tool_ids_arr);
          var anag_tool_names = document.getElementById("anag_tool_names").value;
          var anag_tool_names_arr = anag_tool_names.split(",");
          console.log(tool_names_arr);
        
        var anag_tool = [];
        for (let i = 0; i < anag_tool_ids_arr.length; i++) {
          var new_element = '{"id": ' + anag_tool_ids_arr[i] + ', "name": "' + anag_tool_names_arr[i] + '"}';
          console.log(new_element);
          var new_object = JSON.parse(new_element);
          anag_tool.push(new_object);

        }
        console.log(anag_tool);   

        var team_act = [];
        var act_ids = document.getElementById("act_ids").value;
        var act_ids_arr = act_ids.split(",")
        var act_descs = document.getElementById("act_descs").value;
        var act_descs_arr = act_descs.split("|§|")
        console.log("act_ids:");  
        console.log(act_ids);
        if (act_ids != "" && act_ids != "None") {
          for (let i = 0; i < act_ids_arr.length; i++) {
                var new_element = '{"id": ' + act_ids_arr[i] + ',"name": "' + act_descs_arr[i] + '"}';
                console.log(new_element);
                var new_object = JSON.parse(new_element);
                team_act.push(new_object);
          } 
        }  
        var anag_act_ids = document.getElementById("anag_act_ids").value;
        console.log("anag_act_ids: " + anag_act_ids);
        var anag_acts = [];
        if (anag_act_ids) {
            var anag_act_ids_arr = anag_act_ids.split(",");
            console.log(anag_act_ids_arr);
            var anag_act_descs = document.getElementById("anag_act_descs").value;
            var anag_act_descs_arr = anag_act_descs.split("|§|");
            console.log(anag_act_descs_arr);
            console.log("anag_act_ids_arr.length:");
            console.log(anag_act_ids_arr.length);
        
            for (let i = 0; i < anag_act_ids_arr.length; i++) {
              var new_element = '{"id": ' + anag_act_ids_arr[i] + ', "desc": "' + anag_act_descs_arr[i] + '"}';
              console.log(new_element);
              var new_object = JSON.parse(new_element);
              anag_acts.push(new_object);
            }
        }
        console.log(team_act); 
        
        $("#jsGridPeople").jsGrid({
            width: "40%",
            height: "400px",
            inserting: true, 
            editing: true,
            sorting: true,
            paging: true,
            data: team_people,
                
            fields: [
                { name: "id", title: "Operatore", type: "select", items: anag_people, valueField: "id", textField: "name", width: "50%", align: "left" }, 
                { type: "control" }
            ]
          });

        $("#jsGridTool").jsGrid({
                    width: "40%",
                    height: "400px",
                    inserting: true, 
                    editing: true,
                    sorting: true,
                    paging: true,
                    data: team_tool,
                        
                    fields: [
                        { name: "id", title: "Mezzo", type: "select", items: anag_tool, valueField: "id", textField: "name", width: "50%", align: "left" }, 
                        { type: "control" }
                    ]
                  });

        $("#jsGridAct").jsGrid({
                    width: "40%",
                    height: "400px",
                    inserting: true, 
                    editing: true,
                    sorting: true,
                    paging: true,
                    data: team_act,
                        
                    fields: [
                        { name: "id", title: "Attività", type: "select", items: anag_acts, valueField: "id", textField: "desc", width: "50%", align: "left" }, 
                        { type: "control" }
                    ]
                  });


//Sono costretto a copiare le due SELECT in campi INPUT perché le prime non vengono passate
    //nella request.form (non capisco perché i campi INPUT sì)
    function afterSubmit() {
        //Qui passo il contenuto della jsgrid (le persone) come unica stringa 
        //nel campo nascosto peoples per il passaggio a Python
        var data = $("#jsGridPeople").jsGrid("option", "data");
        var people_ids_Str = "";
        for (let i = 0; i < data.length; i++) {
          var jsonObject = data[i];
          if (people_ids_Str != "") {
            people_ids_Str = people_ids_Str + ",";
          }
          people_ids_Str = people_ids_Str + jsonObject["id"];
        }
        console.log("people_ids_Str: "+people_ids_Str);
        document.getElementById("people_ids").value = people_ids_Str;
      
        //Similmente per la jsgrid dei mezzi 
        var data = $("#jsGridTool").jsGrid("option", "data");
        var tool_ids_Str = "";
        for (let i = 0; i < data.length; i++) {
          var jsonObject = data[i];
          if (tool_ids_Str != "") {
            tool_ids_Str = tool_ids_Str + ",";
          }
          tool_ids_Str = tool_ids_Str + jsonObject["id"];
        }
        console.log("tool_ids_Str: " + tool_ids_Str);
        document.getElementById("tool_ids").value = tool_ids_Str;

        //Similmente per la jsgrid delle attività
        var data = $("#jsGridAct").jsGrid("option", "data");
        var act_ids_Str = "";
        for (let i = 0; i < data.length; i++) {
          var jsonObject = data[i];
          if (act_ids_Str != "") {
            act_ids_Str = act_ids_Str + ",";
          }
          act_ids_Str = act_ids_Str + jsonObject["id"];
        }
        console.log("act_ids_Str: " + act_ids_Str);
        document.getElementById("act_ids").value = act_ids_Str;
  }

  function setTeamAct() {
            var date = document.getElementById("date").value
            $.ajax({
            type: "POST",
            url: "/team_sel_acts" + "/" + date,
            contentType: "application/json",
            dataType: 'json',
            success: function(result) {
              document.getElementById("anag_act_ids").value = result['act_id'];
              document.getElementById("anag_act_descs").value = result['act_desc'];
              console.log("result:");
              console.log(result['act_id']);
              console.log(result['act_desc']);
              load_gridAct();
            } 
          }); 
      }

function load_gridAct() {
    var team_act = [];
    var anag_acts = [];
    var anag_act_ids = document.getElementById("anag_act_ids").value;
        console.log("anag_act_ids: " + anag_act_ids);
        var anag_acts = [];
        if (anag_act_ids) {
            var anag_act_ids_arr = anag_act_ids.split(",");
            console.log(anag_act_ids_arr);
            var anag_act_descs = document.getElementById("anag_act_descs").value;
            var anag_act_descs_arr = anag_act_descs.split("|§|");
            console.log(anag_act_descs_arr);
            console.log("anag_act_ids_arr.length:");
            console.log(anag_act_ids_arr.length);
        
            for (let i = 0; i < anag_act_ids_arr.length; i++) {
              var new_element = '{"id": ' + anag_act_ids_arr[i] + ', "desc": "' + anag_act_descs_arr[i] + '"}';
              console.log(new_element);
              var new_object = JSON.parse(new_element);
              anag_acts.push(new_object);
            }
        }

    $("#jsGridAct").jsGrid({
                    width: "40%",
                    height: "400px",
                    inserting: true, 
                    editing: true,
                    sorting: true,
                    paging: true,
                    data: team_act,
                        
                    fields: [
                        { name: "id", title: "Attività", type: "select", items: anag_acts, valueField: "id", textField: "desc", width: "50%", align: "left" }, 
                        { type: "control" }
                    ]
                  });
}

       