import { Pannellum } from "pannellum-react";
import { useState } from "react";

export function Panorama() {
  const Scenes = {
    image1: {
      title: "View-1",
      image: './images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img1.jpg',
      pitch: -11,
      yaw: -3,
      hotSpot: {
        nexScene: {
          type: "custom",
          pitch: -8,
          yaw: 12,
          cssClass: "moveScene",
          scene: "image2"
        }
      }
    },
    image2: {
      title: "View-2",
      image: './images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img2.jpg',
      pitch: 10,
      yaw: 180,
      hotSpot: {
        scene: "image1"
      }
    },

    image3: {
      title: "View-3",
      image: './images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img1.jpg',
      pitch: 10,
      yaw: 180,
      hotSpot: {
        scene: "image3"
      }
    },

    image4: {
      title: "View-4",
      image: './images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img2.jpg',
      pitch: 10,
      yaw: 180,
      hotSpot: {
        scene: "image4"
      }
    },

    image5: {
      title: "View-5",
      image: './images/e89c9584-eb23-4e1b-aa13-0c1af972ba44/img1.jpg',
      pitch: 10,
      yaw: 180,
      hotSpot: {
        scene: "image5"
      }
    }
  };

  const [scene, setScene] = useState(Scenes.image1);

  return (
    <div>
      <Pannellum
        width={"100%"}
        height={"100vh"}
        title={scene.title}
        image={scene.image}
        pitch={0.28}
        yaw={0}
        hfov={130}
        autoLoad
        showControls={false}
        showFullscreenCtrl={false}
        showZoomCtrl={false}
        orientationOnByDefault={true}
      >
        <Pannellum.Hotspot
          type="custom"
          pitch={15}
          yaw={100}
          name="image1"
          handleClick={(evt, name) => setScene(Scenes.image1)}
        />

        <Pannellum.Hotspot
          type="custom"
          pitch={15}
          yaw={-1}
          name="image2"
          handleClick={(evt, name) => setScene(Scenes.image2)}
        />

        <Pannellum.Hotspot
          type="custom"
          pitch={15}
          yaw={60}
          name="image3"
          handleClick={(evt, name) => setScene(Scenes.image3)}
        />

        <Pannellum.Hotspot
          type="custom"
          pitch={15}
          yaw={140}
          name="image4"
          handleClick={(evt, name) => setScene(Scenes.image4)}
        />

        <Pannellum.Hotspot
          type="custom"
          pitch={15}
          yaw={250}
          name="image5"
          handleClick={(evt, name) => setScene(Scenes.image5)}
        />
      </Pannellum>
    </div>
  );
}
