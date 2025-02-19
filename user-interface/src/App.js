import './App.css';
import React, {useState, useEffect} from 'react';
import { Map } from './components/Map.js';
import { Panorama } from './components/Panorama.js';


function App() {
  
  const [panorama, setPanorama] = useState();
  const [locationName, setLocationName] = useState('unnamed location')
  const [pins, setPins] = useState([])
  const [objects, setObjects] = useState([])
  const [enviroments, setEnvirorements] = useState()
  const [platformActive, setPlatformActive] = useState(1) // 1 for active, 2 for test, 0 for deactive
  
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

  const refreshJSON = () => {
    fetch("/getJSONfilenames").then(
      res => res.json()
    ).then(
      data => {
        setEnvirorements(data)
        console.log(enviroments)
      }
    )
  }

  useEffect(()=> {
    refreshJSON()
  }, [])
  
  useEffect(()=> {
    const interval = setInterval(() => {
      refreshData();
    }, 1000);

    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
    }, [])

  const updatePlatformActiveStatus = async () => {
      if (platformActive == 0) {
        setPlatformActive(1)
      } else if (platformActive == 1) {
        setPlatformActive(0)
      }
      
      try {
        const resp = await fetch("/updatePlatformActiveStatus", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({status: platformActive}),
        });
      } catch (error) {
        console.log(error)
      }
  };

  return (
  
    <div className='container'>
  
      <div className='header'>

        <div className="dropdown">
          <label for="options">Choose a map:</label>
          <select id="options">

            {enviroments?.map((item, index) => (
                <option value={item}>{item}</option>
            ))}
          </select>
          </div>
        
        <button className={platformActive == 1 ? 'button-on' : 'button-off'} onClick={updatePlatformActiveStatus}>⏻</button>

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
