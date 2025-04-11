// This files creates a Panorama component, which shows stitched images and the position of objects in the enviroment
import React, {useState, useEffect} from 'react';
import '../styles/Panorama.css';
import { Pannellum } from "pannellum-react";

export function Panorama({panorama, setPanorama, selectedEnviroment, hsiManualScan, setHSIManualScan,   objects, locationName, setShowHSI, setSearchObjects, searchObjects, selectedPin, setTargetObject}) {

    const [showRGB, setShowRGB] = useState(true)
    const [showObjects, setShowObjects] = useState(false) // Whether objects are shown 
    const [showHSIClassification, setShowHSIClassification] = useState(false)
    const [showNVDI, setShowNDVI] = useState(false)
    const [showNDMI, setShowNDMI] = useState(false)
    const [showMSAVI, setShowMSAVI] = useState(false)
    const [showCustom, setShowCustom] = useState(false)
    const [showArtificial, setShowArtifical] = useState(false)
    const [showHSIRGB, setShowHSIRGB] = useState(false)

    const [searchInput, setSearchInput] = useState('') // Input to search for a new object
    const [hsiScan, setHsiScan] = useState(false) // Wether the new object should be scanned

    // If enter pressed, add new object
    const handleNewSearchObject = async (event) => {
        const newEntry = {
            object: searchInput,
            hsi: hsiScan
        }

        if (event.keyCode == 13) {
            setSearchObjects((prevItems) => [...prevItems,  newEntry])
            setSearchInput('')
            setHsiScan(false)
        } 
    }

    // If X pressed, delete this object
    const handleDeleteObject = async (index) => {
        setSearchObjects((prevItems) => prevItems.filter((_, i) => i !== index));
    }
    
    // Every second, send current object array to back end
    const updateSearchObjects = async () => {
        if (searchObjects) {
            try {
                fetch("/updateObjects", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({objects: searchObjects, hsiManualScan: hsiManualScan})
            })} catch (err) {
                console.log(err)
           }

        }
    }

    useEffect(()=> {
        const interval = setInterval(() => {
            updateSearchObjects();
    }, 200); // If this interval is greater than App.js interval, the code will not execute. Keep it small for field testing, and large for demo.
        return () => clearInterval(interval);
    }, [updateSearchObjects])


    // On click, open further details regarding the object
    const handleHotspot = (obj) => {
        setShowHSI(true)
        setTargetObject(obj)
    }

    const handleToggle = (setButton) => {
        // Reset states
        setShowHSIClassification(false)
        setShowNDVI(false)
        setShowNDMI(false)
        setShowObjects(false)
        setShowRGB(false)
        setShowMSAVI(false)
        setShowCustom(false)
        setShowArtifical(false)
        setShowHSIRGB(false)

        // set target state to true
        setButton(true)
    }

    useEffect(()=>{
        handleToggle(setShowRGB)
        if (selectedEnviroment) {
            setPanorama('./images/' + selectedEnviroment.slice(0, -5) + selectedPin?.panorama_ref)
        }
    }, [selectedPin])
    

    useEffect(()=> {
    if (selectedEnviroment && selectedPin) {
            var suffix = null
        if (showObjects || showRGB ) {
            suffix = selectedPin?.panorama_ref
        } else if (showNVDI) {
            suffix = selectedPin?.ndvi_ref
        } else if (showHSIClassification) {
            suffix = selectedPin?.hsi_ref
        } else if (showMSAVI) {
            suffix = selectedPin?.msavi_ref
        } else if (showCustom){
            suffix = selectedPin?.custom2_ref
        } else if (showArtificial){
            suffix = selectedPin?.artificial_ref
        } else if (showHSIRGB) {
            suffix = selectedPin?.rgb_ref
        }
        if (suffix != null) {
            console.log('updating panorama')
            setPanorama('./images/' + selectedEnviroment.slice(0, -5) + suffix)
        }
       }
        
    }, [showRGB, showObjects, showHSIClassification, showNDMI, showNVDI, showMSAVI, showCustom, showArtificial, showHSIRGB])
        
    return (
        <div className='panorama-container'>
            <h1 style={{fontWeight: 'lighter', position: 'absolute', left: '5px', top: '30px', color: 'white', zIndex: 100, fontSize: '16px'}}>Lon/Lat: {selectedPin?.geo_coords} </h1>

            <div style={{position: 'absolute', right: '5px', top: '5px', zIndex: 100, display: 'flex', flexDirection: 'column'}}>
                <button style={{paddingLeft: '15x', paddingRight: '15px', borderRadius: '5px', fontSize: '16px', fontWeight: 'lighter', backgroundColor: hsiManualScan ? 'black':'transparent', color: hsiManualScan ? 'white':'black'}} onClick={()=> setHSIManualScan(!hsiManualScan)}>Full HSI</button>
                {searchObjects?.map((item, index)=> (
                    <div key={index} style={{backgroundColor: 'black', borderRadius: '5px', margin: '5px', padding: '5px', flexDirection: 'row', display: 'flex', justifyContent: 'space-between', }}>
                         <input type="checkbox" disabled={true} checked={item.hsi} style={{width: '15px', height: '15px', accentColor: 'grey', alignSelf: 'center'}}/>
                        <text style={{color: 'white', fontWeight: 'lighter', marginLeft: '15px', marginRight: '15px',}}>{item.object}</text>
                        <button style={{backgroundColor: 'white', opacity: 0.5, fontWeight: 'bold',borderWidth: '0.5px', borderRadius: '5px'}} onClick={()=>handleDeleteObject(index)}>x</button>
                    </div>
                ))}

            </div>

            {panorama ? (
                // <img src={panorama} alt='Dynamic' className='panorama'/>
                <div style={{backgroundColor: 'black', width: '100%', height: '100%'}}>
                    <Pannellum
                        width={"100%"}
                        height={"100vh"}
                        image={panorama}
                        haov={showRGB|| showObjects ? 358 : 220}
                        vaov={showRGB|| showObjects ? 60 : 30}
                        yaw={showRGB|| showObjects ? 225 : 0}
                        autoLoad={true}
                        autoRotate={0}
                        showControls={false}
                        showFullscreenCtrl={false}
                        showZoomCtrl={false}
                        orientationOnByDefault={true}
                    >

                    {showObjects ? (
                        objects?.map((obj) => (
                            <Pannellum.Hotspot
                            type="custom"
                            pitch={(obj.y/815)*-1*30}
                            yaw={(obj.x/6399)*179}
                            title="1"
                            text={obj.RGB_classification}
                            tooltip={(hotSpotDiv) => {
                                obj?.HS_classification_ref ? hotSpotDiv.classList.add("custom-hotspot-blue") : hotSpotDiv.classList.add("custom-hotspot");
                                obj?.HS_classification_ref ? hotSpotDiv.innerHTML = `<div class="custom-hotspot-inner-blue"/><h1 class="hotspot-text">${obj.RGB_classification}<h1/>`
                                : hotSpotDiv.innerHTML =  `<div class="custom-hotspot-inner"/><h1 class="hotspot-text">${obj.RGB_classification}<h1/>`;
                              }}
                    
                            handleClick={() => handleHotspot(obj)}/> 
                    ))
                    ) : <div/>}
                </Pannellum>
                
                </div>
                
                
            ) : 
            <p style={{color: 'white', margin: '10px', alignSelf:'center', justifySelf: 'center'}}>Select a location from the map</p>
            }
            
            <div className='bottomBar'>
                <h1>{locationName}</h1>
                <h1>|</h1>
                <h2>Select Overlay:</h2>
                {selectedPin?.panorama_ref ? (
                    <h2 style={{color: showRGB?'white':'grey'}} onClick={()=>handleToggle(setShowRGB)}>RGB</h2>
                ):<div/>}
                {selectedPin?.panorama_ref ? (
                    <h2 style={{color: showObjects?'white':'grey'}} onClick={()=>handleToggle(setShowObjects)}>Objects</h2>
                ):<div/>}
                {selectedPin?.hsi_ref ? (
                <h2 style={{color: showHSIClassification?'white':'grey'}} onClick={()=>handleToggle(setShowHSIClassification)}>HSI Classification</h2>
                ):<div/>}
                {selectedPin?.ndvi_ref ? (
                <h2 style={{color: showNVDI?'white':'grey'}} onClick={()=>handleToggle(setShowNDVI)}>NDVI</h2>
                ):<div/>}
                {selectedPin?.ndmi_ref ? (
                <h2 style={{color: showNDMI?'white':'grey'}} onClick={()=>handleToggle(setShowNDMI)}>NDMI</h2>
                ):<div/>}
                <div className='search-input'>
                    <input style={{width: '100%', backgroundColor: 'transparent', color: 'white', fontSize: '20px', fontWeight: 'lighter', borderColor: 'transparent', fontFamily: 'inherit', left: '5px'}} placeholder='Search for...' value={searchInput} onChange={(event)=>{setSearchInput(event.target.value)}} onKeyDown={handleNewSearchObject}/>
                    <div style={{display: 'flex', flexDirection: 'row', position: 'absolute', right: '20px', height: '100%'}}> 
                        <h1 style={{color: 'white', fontSize: '16px'}}>HSI Scan?</h1>
                        <input type="checkbox" onClick={()=>{setHsiScan(!hsiScan)}} checked={hsiScan} style={{width: '15px', height: '15px', accentColor: 'grey', alignSelf: 'center'}}/>
                    </div>  
                </div>
            </div>
        </div>
    );
}
