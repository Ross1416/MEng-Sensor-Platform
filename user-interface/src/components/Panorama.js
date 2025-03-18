import React, {useState, useEffect, useRef} from 'react';
import '../styles/Panorama.css';
import { Pannellum } from "pannellum-react";

export function Panorama({panorama, objects, locationName, setLocationName, selectedEnviroment, setShowHSI, setHSIData}) {


    const [showObjects, setShowObjects] = useState(false)
    const [showMaterials, setShowMaterials] = useState(false)
    const [showDistances, setShowDistances] = useState(false)
    const [showConfidence, setShowConfidence] = useState(false)
    const [edit, setEdit] = useState(false)
    const [reset, setReset] = useState(false)
    const [download, setDownload] = useState(false)
    const [connected, setConnected] = useState(false)

    // Toggle button change
    const toggleButton = (state, stateFunction) => {
        stateFunction(!state)
    }

    const testObjects = [{RGB_classification: 'dog', x: -3633, y: 237,}, {RGB_classification: 'dog', x: 1792, y: 643}]

      
    return (
        <div className='panorama-container'>
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
                    {objects?.map(({x, y, width, height}) => (
                
                        <Pannellum.Hotspot
                            type="custom"
                            pitch={(y/850)*30}
                            yaw={(x/6453)*179}
                            title="1"
                            tooltip={(hotSpotDiv) => {
                                hotSpotDiv.classList.add("custom-hotspot");
                                hotSpotDiv.style.width = width+"px";  // Set custom width
                                hotSpotDiv.style.height = height+"px"; // Set custom height
                            }}
                    
                            handleClick={() => setShowHSI(true)}
                        />
    
                
                    ))}
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
                <button style={{color: showMaterials?'white':'grey', fontSize: "18px"}} height="30px" width="30px" onClick={() => toggleButton(showMaterials, setShowMaterials)}>
                    Show Materials
                </button>
                <button style={{color: showDistances?'white':'grey', fontSize: "18px"}} height="30px" width="30px" onClick={() => toggleButton(showDistances, setShowDistances)}>
                    Show Distances
                </button>
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
