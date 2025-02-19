import './App.css';
import React, {useState, useEffect} from 'react';
import { Map } from './components/Map.js';
import { Panorama } from './components/Panorama.js';

function App() {
  
  const [panorama, setPanorama] = useState();
  const [locationName, setLocationName] = useState('unnamed location')
  const [pins, setPins] = useState([])
  const [objects, setObjects] = useState([])
  
  const refreshData = () => {
    fetch("/getData").then(
      res => res.json()
    ).then(
      data => {
        setLocationName(data.location)
        setPins(data.pins)
      }
    )
  }

  const updateLocationName = async () => {
    try {
      const res = await fetch("/updateLocationName", {
        method: "POST",
        body: JSON.stringify({location: 'New Location' }),
      });
    } catch (error) {
      console.log(error)
    }
  };

  useEffect(()=> {
    const interval = setInterval(() => {
      refreshData();
      updateLocationName();
    }, 5000);

    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
    }, [])

  return (
  
    <div className='container'>
      {/* <button onClick={searchNewPins}>Press me biatch</button> */}
      <div className='header'>
        <div className='search'>
          <button>{'<'}</button>
          <button>{'>'}</button>
          <input placeholder='Search...'/> 
          <button>{'↵'}</button>
        </div>
        <h1>HYPERBOT</h1>
        
      </div>
      <div className='body'>
        <div className='map-container'>
          <Map setPanorama={setPanorama} pins={pins} setPins={setPins} setObjects={setObjects}/>
        </div>

        <div className='panoramic-container'>
          <Panorama panorama={panorama} locationName={locationName} setLocationName={setLocationName} objects={objects}/>
        </div>

      </div>
    </div>
  );
}

export default App;
