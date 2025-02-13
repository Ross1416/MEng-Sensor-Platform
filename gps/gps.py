import serial
import pynmea2
import math
import time
import numpy as np

class Neo6M:
    def __init__(self, port="/dev/ttyAMA0", baudrate=9600, timeout=1, distance_threshold=10, movement_callback=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = serial.Serial(port, baudrate, timeout=timeout)
        self.distance_threshold = distance_threshold
        self.last_location = (0,0)
        self.movement_callback = movement_callback

        #TO REMOVE
        self._dummy_coords_index = 0
        self._dummy_x_coords = np.linspace(55.844216,55.853709,50)
        self._dummy_y_coords = np.linspace(-4.245121,-4.233920,50)

    def read_raw_data(self):
        """Reads raw NMEA sentence from the GPS module. Returns Raw NMEA sentence as a string or None if no data is available."""
        try:
            raw_data = (
                self.connection.readline().decode("utf-8", errors="ignore").strip()
            )
            return raw_data
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        return None

    def get_location(self):
        """Reads and parses the GPS location from NMEA sentences. Returns Dictionary containing latitude, longitude, altitude, and fix quality or None if no fix."""
        count = 0
        while True:
            raw_data = self.read_raw_data()
            if raw_data and raw_data.startswith("$GPGGA"):  # GGA contains location data
                try:
                    msg = pynmea2.parse(raw_data)
                    if msg.latitude and msg.longitude:
                        return {
                            "latitude": msg.latitude,
                            "longitude": msg.longitude,
                            "altitude": msg.altitude,
                            "fix_quality": msg.gps_qual,
                        }
                except pynmea2.ParseError:
                    pass
                    
            if count > 20:
                return None
            else:
                count += 1
    
    def haversine(self, pos1, pos2):
        """Calculates distance in meters between two GPS coordinates.
        pos1 = (lat1,lon1)
        pos2 = (lat2,lon2)"""
        lat1, lon1 = pos1
        lat2, lon2 = pos2
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        return R * c  # Distance in meters

    def wait_for_movement(self):
        """Holds until distance moved > {distance_threshold} and triggers callback function if provided and exits."""
        while distance_moved < self.distance_threshold:
            location = self.get_location()
            if location:
                distance_moved = self.haversine(location, self.last_location)
                
                if distance_moved >= self.distance_threshold:
                    if self.movement_callback:
                        self.movement_callback(location)
                
            time.sleep(1)

    def get_dummy_gps_coords(self):
        self._dummy_coords_index += 1
        if self._dummy_coords_index > 49:
            print("At end of dummy coords")
            return (self._dummy_x_coords[49],self._dummy_y_coords[49])
        else:
            return (self._dummy_x_coords[self._dummy_coords_index],self._dummy_y_coords[self._dummy_coords_index])

    def close(self):
        """Closes the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()


if __name__ == "__main__":
    gps = Neo6M(port="/dev/ttyAMA0")

    location = gps.get_location()
    if location:
        print(
            f"Latitude: {location['latitude']}, Longitude: {location['longitude']}, Altitude: {location['altitude']}m, Fix Quality: {location['fix_quality']}"
        )
    else:
        print("No GPS fix.")

    gps.close()
