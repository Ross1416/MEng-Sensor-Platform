import React, {useState, useEffect, useRef} from 'react';
import '../styles/Panorama.css';
import { Pannellum } from "pannellum-react";

export function Panorama({panorama, objects, locationName, setLocationName, selectedEnviroment, setShowHSI, setHSIData, setSearchObjects, searchObjects, selectedPinInfo, setTargetObject}) {


    const [showObjects, setShowObjects] = useState(true)
    const [showMaterials, setShowMaterials] = useState(false)
    const [showDistances, setShowDistances] = useState(false)
    const [showConfidence, setShowConfidence] = useState(false)
    const [edit, setEdit] = useState(false)
    const [reset, setReset] = useState(false)
    const [download, setDownload] = useState(false)
    const [connected, setConnected] = useState(false)
    const [searchInput, setSearchInput] = useState('')

    // Toggle button change
    const toggleButton = (state, stateFunction) => {
        stateFunction(!state)
    }

    const handleNewSearchObject = async (event) => {

        if (event.keyCode == 13) {
            setSearchObjects((prevItems) => [...prevItems, searchInput])
            setSearchInput('')
        } 
    }

    
    const handleDeleteObject = async (index) => {
        setSearchObjects((prevItems) => prevItems.filter((_, i) => i !== index));
    }
    
    const updateSearchObjects = () => {
        if (searchObjects) {
            try {
                fetch("/updateObjects", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({objects: searchObjects})
            })} catch (err) {
                console.log(err)
           }

        }
    }


    useEffect(()=> {
        const interval = setInterval(() => {
          updateSearchObjects();
    }, 50);
        return () => clearInterval(interval);
    }, [updateSearchObjects])


    const handleHotspot = (obj) => {
        setShowHSI(true)
        setTargetObject(obj)
    }
        
    return (
        <div className='panorama-container'>
            
            <h1 style={{fontWeight: 'lighter',position: 'absolute', left: '5px', top: '5px', color: 'white', zIndex: 100, fontSize: '16px'}}>Timestamp: {selectedPinInfo ? selectedPinInfo.timestamp : ''}</h1>
            <h1 style={{fontWeight: 'lighter', position: 'absolute', left: '5px', top: '30px', color: 'white', zIndex: 100, fontSize: '16px'}}>Lon/Lat: {selectedPinInfo ? selectedPinInfo.coords[0] : ''} </h1>

            <div style={{position: 'absolute', right: '5px', top: '5px', zIndex: 100,  display: 'flex', flexDirection: 'column'}}>
                {searchObjects?.map((item, index)=> (
                    <div key={index} style={{backgroundColor: 'black', minWidth: '80px', borderRadius: '5px', margin: '5px', padding: '5px', flexDirection: 'row', display: 'flex', justifyContent: 'space-between'}}>
                        <text style={{color: 'white', fontWeight: 'lighter'}}>{item}</text>
                        <button style={{backgroundColor: 'white', opacity: 0.5, fontWeight: 'bold',borderWidth: '0.5px', borderRadius: '5px'}} onClick={()=>handleDeleteObject(index)}>x</button>
                    </div>
                ))}

            </div>

            {/* <button onClick={changeScene}>PRESS ME</button> */}
            {panorama ? (
                // <img src={panorama} alt='Dynamic' className='panorama'/>
                <div style={{backgroundColor: 'black', width: '100%', height: '100%'}}>
                    <Pannellum
                        width={"100%"}
                        height={"100vh"}
                        // title={scene.title}
                        image={panorama}
                        haov={358}
                        vaov={60}
                        autoLoad={true}
                        autoRotate={0}
                        showControls={false}
                        showFullscreenCtrl={false}
                        showZoomCtrl={false}
                        orientationOnByDefault={true}
                    >

                    {showObjects ? (
                    // objects?.map(({ x, y, width, height, RGB_classification }) => (
                        objects?.map((obj) => (
                            <Pannellum.Hotspot
                            type="custom"
                            pitch={(obj.y/850)*30}
                            yaw={(obj.x/6453)*179}
                            title="1"
                            text={obj.RGB_classification}
                            tooltip={(hotSpotDiv) => {
                                hotSpotDiv.classList.add("custom-hotspot");
                                // hotSpotDiv.classList.add("custom-hotspot-inner");
                                hotSpotDiv.innerHTML = `<div class="custom-hotspot-inner"/>
                                <h1 class="hotspot-text">${obj.RGB_classification}<h1/>`;
                              }}
                    
                            handleClick={() => handleHotspot(obj)}/> 
                            
                    ))
                    ) : <div/>}
                </Pannellum>
                
                
                </div>
                
                
            ) : 
            <p style={{color: 'white', margin: '10px', alignSelf:'center', justifySelf: 'center'}}>Select a location from the map</p>
            }

            {/* {objects?.map((item, index) => (
                <div  onClick={()=>alert('Clicked')} className="overlay-square" style={{left: item.x1, top: item.y1, right: item.x2, bottom: item.y2, display: showMaterials || showObjects?'block':'none'}}>
                    <p>{showObjects ? item.RGB_classification : ''}</p>
                    <p>{showMaterials ? String(item.HS_classification) : ''}</p>
                    <p>{showDistances ? item.distance + ' m': ''}</p>
                </div>
            ))} */}
            
            <div className='bottomBar'>
                <h1>{locationName}</h1>
                {/* https://react-ionicons.netlify.app/ */}
                <button style={{color: showObjects?'white':'grey', fontSize: "18px"}} height="30px" width="30px" onClick={() => toggleButton(showObjects, setShowObjects)}>
                    Show Objects
                </button>
                {/* <button style={{color: showMaterials?'white':'grey', fontSize: "18px"}} height="30px" width="30px" onClick={() => toggleButton(showMaterials, setShowMaterials)}>
                    Show Materials
                </button>
                <button style={{color: showDistances?'white':'grey', fontSize: "18px", fontWeight: 'lighter'}} height="30px" width="30px" onClick={() => toggleButton(showDistances, setShowDistances)}>
                    Show Distances
                </button> */}
                <input placeholder='Search for...' style={{backgroundColor: 'transparent', borderColor: 'transparent', fontSize: '18px', color: 'white'}} value={searchInput} onChange={(event)=>{setSearchInput(event.target.value)}} onKeyDown={handleNewSearchObject}>
                    
                </input>
                {/* <button>
                    <CubeOutline color={showObjects ? 'white' : '#00000'} height="30px" width="30px" onClick={() => toggleButton(showObjects, setShowObjects)}/>
                </button> */}
                {/* <button>
                    <LayersOutline color={showMaterials ? 'white' : '#00000'} height="30px" width="30px" onClick={() => toggleButton(showMaterials, setShowMaterials)}/>
                </button>
                <button>
                    <PinOutline color={showDistances ? 'white' : '#00000'} height="30px" width="30px"onClick={() => toggleButton(showDistances, setShowDistances)}/>
                </button>
                <button>
                    <ThermometerOutline color={showConfidence ? 'white' : '#00000'} height="30px" width="30px"onClick={() => toggleButton(showConfidence, setShowConfidence)} />
                </button>
                <button>
                    <BrushOutline color={edit ? 'white' : '#00000'} height="30px" width="30px" onClick={() => toggleButton(edit, setEdit)}/>
                </button>
                <button>
                    <ArrowDownCircleOutline color={download ? 'white' : '#00000'} height="30px" width="30px" onClick={() => toggleButton(download, setDownload)}/>
                </button>
                <button>
                    <RefreshOutline color={reset ? 'white' : '#00000'} height="30px" width="30px" onClick={() => toggleButton(reset, setReset)} />
                </button>
                <button>
                    <RadioOutline color={connected ? 'white' : '#00000'} height="30px" width="30px" onClick={() => toggleButton(connected, setConnected)} />
                </button> */}

            </div>
        </div>
    );
}
