// This files creates a Map component, which shows the coordinates of each scan

import React, {useState, useEffect, useRef} from 'react';
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import '../styles/Map.css';
import 'leaflet/dist/leaflet.css';
import L from "leaflet";


export function Map({setPanorama, pins, setObjects, selectedEnviroment, setSelectedPin}) {
    const [mapCenter, setMapCenter] = useState([55.851771, -4.2379665]) // map center - default to Glasgow

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

    // Update the panorama component when a pin is clicked 
    const handlePinClick = (pin) => {
      setSelectedPin(pin)
      setObjects(pin.objects)
    };

    useEffect(()=> {
      if (pins) {
        console.log('updated')
        setMapCenter(pins[0]?.geo_coords)
      }
    },  [selectedEnviroment])
    
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
                  <Marker key={pin.id} position={pin.geo_coords} icon={pin?.hsi_ref ? customIcon : customIcon2 } eventHandlers={{
                    click: () => handlePinClick(pin),
                  }}>
                  <Popup>
                     {pin.geo_coords[0].toFixed(2)}, {pin.geo_coords[1].toFixed(2)}
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

const customIcon2 = L.divIcon({
  className: "emoji-icon", // Optional CSS for further styling
  html: '<span style="font-size: 30px;">📍</span>', // Adjust the font-size
});