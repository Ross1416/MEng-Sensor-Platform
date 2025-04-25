# MEng-Sensor-Platform

## Product Overview
The developed prototype, RangerSight, shown below, is a vehicle mounted remote sensing platform designed for real-time environmental monitoring in protected natural areas. By leveraging a combination of hyperspectral and conventional RGB imaging, it provides detailed insights into the objects and materials present within its environment while also determining plant health and identification of artificial objects. 

RangerSight combines several systems into a single, cohesive, highly capable product with several notable features: 

•	Remote sensing of vegetation health through hyperspectral imaging technology
•	Detection of obscured or camouflaged man-made objects
•	Real-time mapping with 360° panoramas and GNSS system
•	Detection of specified objects of interest for further analysis
•	Rugged design, simply transferrable between mounts
•	No additional software installation required

![image](https://github.com/user-attachments/assets/e1d5bee7-d17b-4f42-b24a-ef07e53c7cd6)

During routine patrols mounted on National Park service vehicles, RangerSight will collect geo-referenced environmental data. With the onboard processing, park rangers can view the results in real-time to uncover immediate environmental threats or store for later analysis. With this system, data collected across the whole National Park can be accumulated over time, allowing arising issues to be detected early and the underlying cause determined. RangerSight is very simple to deploy, with quick installation on practically any vehicle using a multi-vehicle mounting system. A laptop with a web browser is all that is needed to interact with the user interface and view results. It takes less than five minutes to mount on a vehicle and begin capturing data. Measuring just 400 x 340 x 346 mm and weighing 4.31 kg , mounting is simple and can be accomplished by a single person. 

The custom interface is simple to use, displaying the captured data in an intuitive manner on a webapp shown below and is accessed via connecting to RangerSight’s Wi-Fi hotspot. With this interface, the user can also control the operation of the platform and direct the platform to search for specific objects of interest.

![image](https://github.com/user-attachments/assets/2e631354-a62c-4e66-ad11-b40f2e8b2070)

RangerSight has three primary components: the sensor platform itself with its imaging systems, its multi-vehicle mount and the user interface. A high-level overview of the subsystems which compose RangerSight are detailed below:

![image](https://github.com/user-attachments/assets/e123d728-d5f6-4fa1-84a2-f6d57f9fc770)

At each scan location, RangerSight flows through a data capture and processing pipeline. The figure below demonstrates a simplified flow diagram of the system operation, from the mounting to its delivery of results in the user interface. For further details on how to setup and use the sensor platform, please refer to the attached User Guide.

![image](https://github.com/user-attachments/assets/fd59c0ad-e350-4d9e-8d17-f649362650be)

A list of RangerSight’s key system details is recorded in the table below.

| Detail      | Value |
| ----------- | ----------- |
|Avg. Scan Duration      | 110 to 130 seconds       |
|Avg. Analysis Duration   | 120 to 140 seconds         |
|RGB Imaging System	| 4x RGB Pi Module 3 Cameras, arranged perpendicularly|
|RGB Panorama Resolution |	12506 x 1700 |
|RGB Field of View |	360° horizontal by 60° vertical |
|HS Imaging System | Basler piA1600-35gm, modified with spectrograph|
|HS Resolution	| 1 x 800, orientated via rotational mount|
|HS Field of View |	27° vertically|
|HS Bands |	600 uniformly distributed bands from 400nm (ultraviolet) to 1000nm (near infrared)|
|HS Linewidth | 0.7 nm ± 0.1 nm|
|Mounting options |	Custom multi-vehicle mount or tripod |
|Max Power Consumption |	77 W  |
|Power Source |	External|


