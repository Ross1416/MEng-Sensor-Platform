import React, {useState, useEffect, useRef} from 'react';
import '../styles/Popup.css';

export function Popup({showHSI, setShowHSI, targetObject, selectedEnviroment}) {

    const [window, setWindow] = useState('overview')
    const [imgSource, setImgSource] = useState('')
    const [hsiData, setHSIData] = useState([])

    const changeWindow = (target) => {
        setWindow(target)
        if (target == 'classification') {
            setImgSource('./images/' + selectedEnviroment.slice(0, -5) + '/' + targetObject.HS_classification_ref)
        } else if (target == 'plant-health') {
            setImgSource('./images/' + selectedEnviroment.slice(0, -5) + '/' + targetObject.HS_ndvi_ref)
        }
    }

    useEffect(()=> {
        setWindow('overview')
    }, [showHSI])


    return (
        
        <div className={showHSI ? 'popup-container-show' : 'popup-container-hide' }>
            <div className='popup-header'>
                    <h1 className='popup-title'>Hyperspectral Analysis</h1> 
                    <button onClick={()=>setShowHSI(false)}>X</button>  
                </div>
            {window=='overview' ? (
                <div className='overview-container' style={{backgroundColor: 'white', width: '100%', height: '400px'}}>
                    <h3>RGB Classification: {targetObject?.RGB_classification} </h3>
                    <h3>RGB Confidence: {targetObject?.RGB_confidence}</h3>
                    {targetObject?.distance && (
                    <h3>Distance: {targetObject?.distance}</h3>)}
                    {targetObject?.HS_materials && (
                    <h3>HSI Classification:</h3>)}
                        {targetObject?.HS_materials && 
                        Object.entries(targetObject?.HS_materials).map(([item, value]) => (
                        <h2 className='hsi-class' key={item}>
                        {item}: {Math.round(Number(value))}%
                        </h2>
                        ))
                    }
                    

                </div>
            ):(
            <div style={{width: '100%', height: '400px', backgroundColor: 'black', alignItems: 'center', justifyContent: 'center', display: 'flex'}}>
                <img src={imgSource} alt='Dynamic' style={{maxWidth: '100%', maxHeight: '100%', objectFit: 'contain'}}/>
            </div>
            )}
            <div className='popup-footer'>
                    <button onClick={()=>changeWindow('overview')} className={window == 'overview' ? 'footer-toggle-on':'footer-toggle-off'}>Overview</button>  
                    {targetObject?.HS_materials && (
                    <button onClick={()=>changeWindow('classification')} className={window == 'classification' ? 'footer-toggle-on':'footer-toggle-off'}>Classification</button>  )}
                    {targetObject?.HS_materials && (
                    <button onClick={()=>changeWindow('plant-health')} className={window == 'plant-health' ? 'footer-toggle-on':'footer-toggle-off'}>Plant Health</button> )}
            </div>
        </div>
    );
}