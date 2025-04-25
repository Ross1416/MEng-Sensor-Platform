// This main file houses all compoennts (./components) and sends information across components.


import './App.css';
import React, {useState, useEffect} from 'react';
import { Map } from './components/Map.js';
import { Panorama } from './components/Panorama.js';
import { Popup } from './components/Popup.js'

function App() {
  
  // ACCESSIBLE DATA 
  const [pins, setPins] = useState(null) // list of pins in the enviroment
  const [objects, setObjects] = useState([]) // list of objects in a pin
  const [enviroments, setEnvirorements] = useState(null) // list of files saved on device

  // SELECTED DATA
  const [locationName, setLocationName] = useState('') // enviroment name
  const [selectedPin, setSelectedPin] = useState(null) // pin timestamp + coordinataes
  const [selectedEnviroment, setSelectedEnviroment] = useState(null) // user selected file 
  const [targetObject, setTargetObject] = useState({}) // selected object information
  const [panorama, setPanorama] = useState('')
  const [showLegend, setShowLegend] = useState('none')

  // INTERFACE CONTROL
  const [showHSI, setShowHSI] = useState(false) // show modal?
  const [createNewEnviroment, setCreateNewEnviroment] = useState(false) // creates a new enviroment
  const [newEnviromentName, setNewEnviromentName] = useState('') // user specified new enviroment name
 
  // DEVICE CONTROL 
  const [platformActive, setPlatformActive] = useState(0) // 1 for active device, 2 for test, 0 for deactive
  const [takePhoto, setTakePhoto] = useState(false) // controls colour of camera button
  const [statusMessage, setStatusMessage] = useState('') // status message contee nt
  const [statusMessageTimestamp, setStatusMessageTimestamp] = useState('') // status message timestamp
  const [searchObjects, setSearchObjects] = useState([])
  const [hsiManualScan, setHSIManualScan] = useState(false)

  // DEVICE ANALYSIS
  const [gpsConnected, setGPSConnected] = useState(false) // is gps connected
  const [piConnected, setPiConnected] = useState(false) // is Pi connected
  const [WIFIConnected, setWIFIConnected] = useState(false)// is WiFi connected

  
  // Poll for data every 200ms
  const refreshData = () => {

    // If the user has selected a file...
    if (selectedEnviroment) {
      try {
        fetch("/getData", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({file: selectedEnviroment}),
        }).then(
          // Proccess data
          resp => resp.json())
        .then( data => {
          // Save data
          setPins(data.pins)
          setLocationName(data.location)
        });
      } catch (error) {
        console.log(error)
      }
    } else {
       // If no file specified, set default file (first run)
      fetch("/getActiveFile").then(resp=>resp.json())
      .then((data) => {
        setSelectedEnviroment(data.activeFile);
        setSearchObjects(data.searchObjects)
    })
    };


    // Poll for sensor platform status
    try {
      fetch("/getPlatformStatus").then(resp=>resp.json())
      .then(resp=> {
        if (statusMessage != resp[0]) {
          const d = new Date().toLocaleTimeString()
          setStatusMessage(resp[0])
          setStatusMessageTimestamp(d)
        }
        setPiConnected(resp[1])
        setGPSConnected(resp[2])
        setWIFIConnected(resp[3])
    })

    } catch (err) {
      console.log(err)
    }
    
    // If user has not selected a panorama yet, set default 
    if (pins && selectedEnviroment && !panorama) {
      try {
        setPanorama('./images/' + selectedEnviroment.slice(0, -5) + pins[0]?.panorama_ref)
        setObjects(pins[0].objects)
        setSelectedPin(pins[0])
      } catch (err) {
        console.log(err)
      }
    }

    // Update available filenames
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
    }, 200);
  
    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
  }, [refreshData])

  
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
  const handleTakePhoto = async () => {
      setTakePhoto(true)
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

      const interval = setInterval(() => {
        setTakePhoto(false);
      }, 1000);
    
      // Cleanup the interval on component unmount
      return () => clearInterval(interval);
  }

  return (
  
    <div className='container'>
      <Popup setShowHSI={setShowHSI} showHSI={showHSI} targetObject={targetObject} selectedEnviroment={selectedEnviroment}/>
  
      <div className='header'>

        <div className='upper-left-buttons'>
          <div className="dropdown">
            <label for="options">Choose a map:</label>
            <select id="options" value={selectedEnviroment} onChange={handleChangeEnviroment}>

              {enviroments?.map((item, index) => (
                  <option value={item.filename}>{item.location}</option>
              ))}
            
            </select>
          </div>
          <button className={createNewEnviroment == 1 ? 'button-on' : 'button-off'} onClick={handleCreateNewEnviroment}>+</button>
          <input className='new-input' placeholder='Name New Enviroment' value={newEnviromentName} onChange={(event)=>{setNewEnviromentName(event.target.value)}} style={createNewEnviroment ? {display: 'block'}:{display: 'none'}}/>
        </div>

        <h1>Current Status: {statusMessage} ({statusMessageTimestamp})</h1>


        <div className='upper-right-buttons'>
          <label for="options">Choose a map:</label>

          <h1 style={{color: WIFIConnected ? 'white':'grey', margin: '5px'}}>WiFi</h1>
          <h1 style={{color: piConnected ? 'white':'grey', margin: '5px'}}>Pi</h1>
          <h1 style={{color: gpsConnected ? 'white':'grey', margin: '5px'}}>GPS</h1> 

          <button className={platformActive == 1 ? 'button-on' : 'button-off'} onClick={updatePlatformActiveStatus}>⏻</button>
          <button className={takePhoto == 1 ? 'button-on' : 'button-off'} onClick={handleTakePhoto}>[◉"]</button>   
        </div>


      </div>
      <div className='body'>
        <div className='map-container'>
          <Map setPanorama={setPanorama} pins={pins} setPins={setPins} setObjects={setObjects} selectedEnviroment={selectedEnviroment} selectedPin={selectedPin} setSelectedPin={setSelectedPin} />
        </div>
        
        <div className='panoramic-container' style={{width: showLegend != 'none' ? '70%' :  '75%'}}>
          <Panorama setShowLegend={setShowLegend} panorama={panorama} hsiManualScan={hsiManualScan} setHSIManualScan={setHSIManualScan} setPanorama={setPanorama} selectedEnviroment={selectedEnviroment} locationName={locationName} setLocationName={setLocationName} objects={objects} selectedEnviroment={selectedEnviroment} setShowHSI={setShowHSI} setSearchObjects={setSearchObjects} searchObjects={searchObjects} selectedPin={selectedPin} setTargetObject={setTargetObject}/>
        </div>

        <img src={showLegend  == 'index' ? './images/nvdi_index.jpg' : './images/classification_legend.png'} className='legend-container' style={{width: showLegend  != 'none' ? '8%' : '0%', backgroundColor: 'black'}}/>
        
      </div> 
    </div>
  );
}

export default App;
