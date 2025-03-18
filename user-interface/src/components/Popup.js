import React, {useState, useEffect, useRef} from 'react';
import '../styles/Popup.css';

export function Popup({showHSI, setShowHSI, hsiData}) {
    return (
        
        <div className={showHSI ? 'popup-container-show' : 'popup-container-hide' }>
            <div className='popup-header'>
                <text></text> 
                <button onClick={()=>setShowHSI(false)}>X</button>  
            </div>
            <img src={'./images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img1.jpg'} alt='Dynamic' className='panorama'/>
        </div>
    );
}