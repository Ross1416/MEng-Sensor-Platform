import React, {useState, useEffect, useRef} from 'react';
import '../styles/Popup.css';

export function Popup({showHSI, setShowHSI, targetObject}) {

    const [window, setWindow] = useState('overview')
    const [imgSource, setImgSource] = useState('./images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/hsi.JPG')
    const [hsiData, setHSIData] = useState([])

    const changeWindow = (target) => {
        setWindow(target)
        if (target == 'classification') {
            setImgSource('./images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/hsi.JPG')
        } else if (target == 'plant-health') {
            setImgSource('./images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img1.JPG')
        }
    }

    useEffect(()=> {
        console.log(targetObject?.HS_classification)
    }, [showHSI])

    const testData = {'wood': 0.5, 'iron':0.3, 'metal': 0.3}

    return (
        
        <div className={showHSI ? 'popup-container-show' : 'popup-container-hide' }>
            <div className='popup-header'>
                    <h1 className='popup-title'>Hyperspectral Analysis</h1> 
                    <button onClick={()=>setShowHSI(false)}>X</button>  
                </div>
            {window=='overview' ? (
                <div className='overview-container' style={{backgroundColor: 'white', width: '100%', height: '100%'}}>
                    <h3>RGB Classification: {targetObject?.RGB_classification} </h3>
                    <h3>RGB Confidence: {targetObject?.RGB_confidence}</h3>
                    <h3>Distance: {targetObject?.distance}</h3>
                    <h3>HSI Classification:</h3>
                        {/* <h2 className='hsi-class'>{targetObject?.HS_classification.keys()}: </h2> */}
                        {Object.entries(testData).map(([item, value]) => (
                        <h2 className='hsi-class' key={item}>
                        {item}: {Number(value*100)}%
                        </h2>
                        ))}
                    

                </div>
            ):(
            <div style={{width: '100%', height: '100%'}}>
                <img src={imgSource} alt='Dynamic' style={{width: '100%', height: '100%'}}/>
            </div>
            )}
            <div className='popup-footer'>
                    <button onClick={()=>changeWindow('overview')} className={window == 'overview' ? 'footer-toggle-on':'footer-toggle-off'}>Overview</button>  
                    <button onClick={()=>changeWindow('classification')} className={window == 'classification' ? 'footer-toggle-on':'footer-toggle-off'}>Classification</button>  
                    <button onClick={()=>changeWindow('plant-health')} className={window == 'plant-health' ? 'footer-toggle-on':'footer-toggle-off'}>Plant Health</button> 
            </div>
        </div>
    );
}