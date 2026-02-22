
console.log("Sono nello script activity/geo_foto.js");
//alert("Sono nello script activity/geo_foto.js");
// 3. Invia a Flask tramite Ajax

$('#cameraInput').on('change', function() {
    const act_id = document.getElementById("act_id").value; 
    const foto_notes = document.getElementById("foto_notes").value;
    // 1. Verifica che sia stato effettivamente selezionato un file
    if (this.files.length === 0) return;

    const file = this.files[0];
    const statusDisplay = $('#foto_status'); // Opzionale: un div per dare feedback all'utente

    statusDisplay.text("Recupero posizione GPS...");

    // 2. Recupera la posizione GPS solo DOPO lo scatto
    navigator.geolocation.getCurrentPosition(function(position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        statusDisplay.text("Invio foto e coordinate...");

        // 3. Prepara il FormData
        var formData = new FormData();
        formData.append('image', file);
        formData.append('lat', lat);
        formData.append('lon', lon);
        formData.append('foto_notes', foto_notes);

        // 4. Invia i dati a Flask
        $.ajax({
            url: "/activity/" + act_id + "/upload_foto",
            type: 'POST',
            data: formData,
            processData: false, 
            contentType: false,
            success: function(data) {
                console.log('Successo:', data);
                statusDisplay.text("Caricamento completato!");
            },
            error: function(xhr, status, error) {
              console.error("Status:", xhr.status); // Es: 404, 500, 413
              console.error("Response:", xhr.responseText);
              alert("Errore " + xhr.status + ": " + error);
            }
        });
    }, function(error) {
        alert("Errore GPS: Assicurati che la localizzazione sia attiva e di usare HTTPS.");
        statusDisplay.text("Errore: GPS non disponibile.");
    }, {
        enableHighAccuracy: true // Forza l'uso del GPS reale invece della cella telefonica
    });
});