import './App.css';
import React, {useState, useEffect} from 'react';
import { Map } from './components/Map.js';
import { Panorama } from './components/Panorama.js';


function App() {
  

  // ENVIROREMENT DATA
  const [panorama, setPanorama] = useState(); // image reference to panorama
  const [locationName, setLocationName] = useState('New Enviroment') // enviroment name
  const [pins, setPins] = useState([]) // pins in the enviroment
  const [objects, setObjects] = useState([]) // objects in a pin
  const [enviroments, setEnvirorements] = useState() // a list of possible enviroments saved on device
  const [selectedEnviroment, setSelectedEnviroment] = useState('scan1.json') // a list of possible enviroments saved on device

  // DEVICE CONTROL
  const [platformActive, setPlatformActive] = useState(1) // 1 for active device, 2 for test, 0 for deactive
  

  const refreshData = async () => {
    try {
      fetch("/getData", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({selectedEnviroment: selectedEnviroment}),
      }).then(
        resp => resp.json())
      .then( data => {
        // console.log(data)
        setPins(data.pins)
        setLocationName(data.location)
      });
    } catch (error) {
      console.log(error)
    }
  }

  // get list of files saved on device
  const recieveFilenames = () => {
    fetch("/getJSONfilenames").then(
      res => res.json()
    ).then(
      data => {
        setEnvirorements(data)
      }
    )
  }

  useEffect(()=> {
    recieveFilenames()
  }, [])
  
  useEffect(()=> {
    const interval = setInterval(() => {
      refreshData();
    }, 1000);
  
    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
  }, [refreshData])

  useEffect(()=>{
    refreshData()
  }, [selectedEnviroment])

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
          <select id="options" value={selectedEnviroment} onChange={(event)=>setSelectedEnviroment(event.target.value)}>

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
        <h1>HYPERBRO</h1>
        
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
