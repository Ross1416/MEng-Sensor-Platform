import React, {useState, useEffect} from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import '../styles/Map.css';
import 'leaflet/dist/leaflet.css';
import L from "leaflet";

// Update Map Coordinates
const UpdateMapCenter = ({ newCenter }) => {
    const map = useMap();
};

export function Map({setPanorama, pins, setPins, setObjects}) {
    
    const [mapCenter, setMapCenter] = useState([55.88000, -4.31000]) // default to London

    // Set co-ords to users location
    useEffect(()=> {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(      
              (position) => {
                const { latitude, longitude } = position.coords;
                setMapCenter([latitude, longitude]);
              },
              (err) => {
                console.log(err);
              }
            );
          }
    }, [])      

    const handlePinClick = (pin) => {
      setPanorama(pin.panorama_ref)
      setObjects(pin.objects)
    };
  
    
    return (
   
      <MapContainer
          className='map'
          center={mapCenter} // Latitude and Longitude (e.g., London)
          zoom={14} // Zoom level
          >
        
          <TileLayer
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
          {pins?.map((pin) => (
                  <Marker key={pin.id} position={pin.geo_coords} icon={customIcon} eventHandlers={{
                    click: () => handlePinClick(pin),
                  }}>
                  <Popup>
                      <strong>{pin.name}</strong> <br /> Coordinates:{" "}
                      {pin.geo_coords.join(", ")}
                  </Popup>
                  </Marker>
              ))}
      </MapContainer>

    );
}

const customIcon = L.divIcon({
    className: "emoji-icon", // Optional CSS for further styling
    html: '<span style="font-size: 30px;">📍</span>', // Adjust the font-size
});