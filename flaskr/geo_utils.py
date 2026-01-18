from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import time

def geocoordinates(address): 
    #Trasforma un indirizzo civico in latitudibe e longitudine
    #print("Sono in geocoordinates")
    error = None
    # 1. Inizializza il geolocalizzatore
    # Nota: inserisci un user_agent personalizzato per rispettare le policy di OSM
    geolocator = Nominatim(user_agent="mio_calcolatore_distanze_v2")
    # 2. Geocodifica indirizzo
    time.sleep(1) # Rispetto del limite di 1 richiesta al secondo
    loc = geolocator.geocode(address)
    #print(loc)
    if not loc:
        error = "L'Indirizzo non è stato trovato."
        lat = None
        lon = None
    else:
        lat, lon = loc.latitude, loc.longitude
    return (lat,lon,error)
    
def road_distance_km(lat1,lon1,lat2,lon2):   
    #Calcola la distanza stradale in Km tra due punti
    # Moltiplica per 2 (Andata/Ritorno) e arrotonda all'intero
    # Utilizza le API pubbliche di OSRM
    try:
        error = None
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        r = requests.get(url)
        data = r.json()
        # La distanza restituita è in metri
        meter_road_distance = data['routes'][0]['distance']
        road_distance = round(meter_road_distance / 1000 * 2) 
    except Exception as e:
        error=f"Errore durante l'esecuzione: {e}"
    return(road_distance,error)
