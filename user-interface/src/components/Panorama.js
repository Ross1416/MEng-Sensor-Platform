import React, {useState, useEffect} from 'react';
import '../styles/Panorama.css';

export function Panorama({panorama, objects, locationName, setLocationName, selectedEnviroment}) {

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


    return (
        <div className='panorama-container'>
            {panorama ? (
                <img src={panorama} alt='Dynamic' className='panorama'/>
                
            ) : 
            <p style={{color: 'white', margin: '10px', alignSelf:'center', justifySelf: 'center'}}>Select a location from the map</p>
            }

            {objects?.map((item, index) => (
                <div  onClick={()=>alert('Clicked')} className="overlay-square" style={{left: item.x1, top: item.y1, right: item.x2, bottom: item.y2, display: showMaterials || showObjects?'block':'none'}}>
                    <p>{showObjects ? item.RGB_classification : ''}</p>
                    <p>{showMaterials ? String(item.HS_classification) : ''}</p>
                    <p>{showDistances ? item.distance + ' m': ''}</p>
                </div>
            ))}
            
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
