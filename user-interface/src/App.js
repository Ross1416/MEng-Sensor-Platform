import './App.css';
import React, {useState, useEffect} from 'react';
import { Map } from './components/Map.js';
import { Panorama } from './components/Panorama.js';


function App() {
  
  // ENVIROREMENT DATA 
  const [panorama, setPanorama] = useState(); // image reference to panorama
  const [locationName, setLocationName] = useState('') // enviroment name
  const [pins, setPins] = useState([]) // list of pins in the enviroment
  const [objects, setObjects] = useState([]) // list of objects in a pin
  const [enviroments, setEnvirorements] = useState() // a list of possible enviroments saved on device
  const [selectedEnviroment, setSelectedEnviroment] = useState(null) // user selected enviroment 

  // DEVICE CONTROL 
  const [platformActive, setPlatformActive] = useState(0) // 1 for active device, 2 for test, 0 for deactive
  const [createNewEnviroment, setCreateNewEnviroment] = useState(false) // press to create new enviroment
  const [newEnviromentName, setNewEnviromentName] = useState('')
  const [searchText, setSearchText] = useState('') 

  // Poll for data updates once every second
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
        console.log(data)
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
  
  useEffect(()=> {
    const interval = setInterval(() => {
      refreshData();
    }, 1000);
  
    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
  }, [refreshData])

  // Get active file on load
  // useEffect(async ()=> {
  //   try {
  //     console.log('got here')
  //     fetch("/getActiveEnviroment").then(
  //       resp => console.log('ACTIVE FILE: ', resp)
  //     // .then( data => {
  //     //   setPins(data.pins)
  //     //   setLocationName(data.location)
  //     //   console.log(data)
  //     // });
  //   )} catch (err) {
  //     console.log(err)
  //   }
  // }, [])


  // Update the platform's status (1 for active, 0 for inactive, 2 for test)
  const updatePlatformActiveStatus = async () => {
      if (platformActive == 0) {
        setPlatformActive(1)
        const resp = await fetch("/updatePlatformActiveStatus", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({status: 1}),
        });
      } else {
        setPlatformActive(0)
        const resp = await fetch("/updatePlatformActiveStatus", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({status: 0}),
        });
      }
  };

  // Alert the back-end that a new enviroment is active 
  const handleChangeEnviroment = async (event) => {
    setSelectedEnviroment(event.target.value)
    try {
      fetch("/updateActiveEnviroment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({file: event.target.value}),
      })
    } catch (error) {
      console.log(error)
    }
  }

  // Request the backend to create a new enviroment
  const handleCreateNewEnviroment = () => {
    if (createNewEnviroment == false) {
      setCreateNewEnviroment(true)
    } else if (newEnviromentName == '') {
      setCreateNewEnviroment(false)
    } else {
      fetch("/createNewEnviroment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({location: newEnviromentName}),
      }).then(
      setCreateNewEnviroment(false))
      .then(
      setNewEnviromentName(''))
    }
  }

  // If the user types in 'Test', perform a one time capture 
  const handleSearch = async () => {
    if (searchText == 'Test') {
      try {
        const resp = await fetch("/updatePlatformActiveStatus", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({status: 2}),
        });
        setPlatformActive(0)
      } catch (error) {
        console.log(error)
      }
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
          <input  value={searchText} onChange={(event)=>{setSearchText(event.target.value)}} placeholder='Search...'/> 
          <button onClick={handleSearch}>{'↵'}</button>
        </div>
        
      </div>
      <div className='body'>
        <div className='map-container'>
          <Map setPanorama={setPanorama} pins={pins} setPins={setPins} setObjects={setObjects} selectedEnviroment={selectedEnviroment} />
        </div>

        <div className='panoramic-container'>
          <Panorama panorama={panorama} locationName={locationName} setLocationName={setLocationName} objects={objects} selectedEnviroment={selectedEnviroment}/>
        </div>

      </div>
    </div>
  );
}

export default App;
