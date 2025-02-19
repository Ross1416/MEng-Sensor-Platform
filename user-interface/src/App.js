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
  const [selectedEnviroment, setSelectedEnviroment] = useState(null) 

  // DEVICE CONTROL
  const [platformActive, setPlatformActive] = useState(1) // 1 for active device, 2 for test, 0 for deactive
  const [createNewEnviroment, setCreateNewEnviroment] = useState(false)
  const [newEnviromentName, setNewEnviromentName] = useState('')

  const refreshData = async () => {
    try {
      fetch("/getData", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({file: selectedEnviroment}),
      }).then(
        resp => resp.json())
      .then( data => {
        setPins(data.pins)
        setLocationName(data.location)
      });
    } catch (error) {
      console.log(error)
    }

    fetch("/getJSONfilenames").then(
      res => res.json()
    ).then(
      data => {
        setEnvirorements(data)
      })
  }
  
  // For polling:
  useEffect(()=> {
    const interval = setInterval(() => {
      refreshData();
    }, 1000);
  
    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
  }, [refreshData])


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
          body: JSON.stringify({file: selectedEnviroment, status: platformActive}),
        });
      } catch (error) {
        console.log(error)
      }
  };

  const handleChangeEnviroment = (event) => {
    console.log(event.target.value)
    setSelectedEnviroment(event.target.value)
  }

  const handleCreateNewEnviroment = () => {
    if (createNewEnviroment == false) {
      setCreateNewEnviroment(true)
    } else if (newEnviromentName == '') {
      setCreateNewEnviroment(false)
    } else {
      fetch("/createNewEnviroment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({file: 'newfile.json', location: newEnviromentName}),
      }).then(
      setCreateNewEnviroment(false))
      .then(
      setNewEnviromentName(''))
    }
  }
  

  return (
  
    <div className='container'>
  
      <div className='header'>

        <div className="dropdown">
          <label for="options">Choose a map:</label>
          <select id="options" value={selectedEnviroment} onChange={handleChangeEnviroment}>

            {enviroments?.map((item, index) => (
                <option value={item.filename}>{item.location}</option>
            ))}
          
          </select>
          </div>
        
        <button className={platformActive == 1 ? 'button-on' : 'button-off'} onClick={updatePlatformActiveStatus}>⏻</button>
        <button className='new-button' onClick={handleCreateNewEnviroment}>+</button>
        <input className='new-input' placeholder='Name New Enviroment' value={newEnviromentName} onChange={(event)=>{setNewEnviromentName(event.target.value)}} style={createNewEnviroment ? {display: 'block'}:{display: 'none'}}/>

        <div className='search'>
          <button>{'<'}</button>
          <button>{'>'}</button>
          <input placeholder='Search...'/> 
          <button>{'↵'}</button>
        </div>
        {/* <h1>HYPERBRO</h1> */}
        
      </div>
      <div className='body'>
        <div className='map-container'>
          <Map setPanorama={setPanorama} pins={pins} setPins={setPins} setObjects={setObjects} />
        </div>

        <div className='panoramic-container'>
          <Panorama panorama={panorama} locationName={locationName} setLocationName={setLocationName} objects={objects} selectedEnviroment={selectedEnviroment}/>
        </div>

      </div>
    </div>
  );
}

export default App;
