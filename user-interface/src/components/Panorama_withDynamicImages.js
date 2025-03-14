import { Pannellum } from "pannellum-react";
import { useState } from "react";

export function Panorama() {

  const Images = {
    image1: './images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img2.jpg',
    image2: './images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img1.jpg'
  }

  const [image, setImage] = useState(Images.image1)
  // const [scene, setScene] = useState(Scenes.image1);

  return (
    <div>
      <Pannellum
        width={"100%"}
        height={"100vh"}
        // title={scene.title}
        image={image}
        haov={358}
        vaov={40}
        autoLoad={true}
        autoRotate={0}
        showControls={false}
        showFullscreenCtrl={false}
        showZoomCtrl={false}
        orientationOnByDefault={true}
      >
        <Pannellum.Hotspot
          type="custom"
          pitch={0}
          yaw={0}
          name="image1"
          handleClick={(evt, name) => setImage(Images.image2)}
        />
      </Pannellum>
    </div>
  );
}
