import urequests
import jpegdec
from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A, MONDAY

from badger2040w import WIDTH, Badger2040W, UPDATE_NORMAL

import secrets
from secrets import HA_BASE_URL, HA_ACCESS_TOKEN


display = Badger2040W()
display.led(128)
display.set_update_speed(UPDATE_NORMAL)
jpeg = jpegdec.JPEG(display.display)
i2c = PimoroniI2C(sda=4, scl=5)
rtc = PCF85063A(i2c)

BLACK = 0
WHITE = 15
IMAGE_WIDTH = 104

display.set_pen(BLACK)
display.clear()
display.connect()

LINE_START_OFFSET = IMAGE_WIDTH + 3
STATUS_VALUE_OFFSET = IMAGE_WIDTH + 25


class HAError(Exception):
    pass


class HAFetchStateError(HAError):
    pass


def fetch_state(entity: str) -> dict:
    headers = {
        "Authorization": f"Bearer {HA_ACCESS_TOKEN}",
        "content-type": "application/json",
    }
    url = f"{HA_BASE_URL}/states/{entity}"
    print("Fetching state from", url)
    res = urequests.get(url, headers=headers)
    if res.status_code != 200:
        msg = f"Error fetching state for {entity}: {res.text}"
        raise HAFetchStateError(msg)
    data = res.json()
    res.close()
    del data["context"]
    print(data)
    return data


class HAPlant:
    def __init__(self):
        self._last_fetched = None
        self.plant_state = None
        # Example state
        # {
        #   "entity_id": "plant.aloe_vera",
        #   "state": "problem",
        #   "attributes": {
        #     "species": "Aloe vera",
        #     "moisture_status": "ok",
        #     "temperature_status": "ok",
        #     "conductivity_status": "Low",
        #     "illuminance_status": "ok",
        #     "humidity_status": null,
        #     "dli_status": "Low",
        #     "species_original": "aloe vera",
        #     "device_class": "plant",
        #     "entity_picture": "https://opb-img.plantbook.io/aloe%20vera.jpg",
        #     "friendly_name": "Aloe vera"
        #   },
        #   "last_changed": "2023-03-10T12:51:29.103630+00:00",
        #   "last_updated": "2023-03-10T12:52:47.188669+00:00",
        # }
        self.details = {}
        # Example illuminance state
        # {
        #   "entity_id": "sensor.aloe_vera_illuminance",
        #   "state": "245",
        #   "attributes": {
        #     "state_class": "measurement",
        #     "unit_of_measurement": "lx",
        #     "device_class": "illuminance",
        #     "friendly_name": "Aloe vera Illuminance"
        #   },
        #   "last_changed": "2023-03-10T13:58:08.838316+00:00",
        #   "last_updated": "2023-03-10T13:58:08.838316+00:00",
        # }

    def get_plant_attribute(self, attribute):
        return self.plant_state.get("attributes", {}).get(attribute, None)

    def get_detailed_state(self, attribute):
        return self.details.get(attribute, {}).get("state", None)

    def get_detailed_attribute(self, attribute, attribute_name):
        return (
            self.details.get(attribute, {})
            .get("attributes", {})
            .get(attribute_name, None)
        )

    def get_plant_status(self, attribute):
        status = self.get_plant_attribute(f"{attribute}_status")
        if status is None:
            return "N/A"
        status = status.upper()
        if status == "OK":
            return "OK"
        detailed_state = self.get_detailed_state(
            attribute
        ) + self.get_detailed_attribute(attribute, "unit_of_measurement")
        if status == "LOW":
            return f"Bas ({detailed_state})"
        if status == "HIGH":
            return f"Haut ({detailed_state})"
        return status

    def fetch_states(self) -> None:
        self.plant_state = fetch_state(secrets.HA_PLANT_ID)
        self.details["moisture"] = fetch_state(secrets.HA_PLANT_MOISTURE_SENSOR)
        self.details["illuminance"] = fetch_state(secrets.HA_PLANT_ILLUMINANCE_SENSOR)
        self.details["temperature"] = fetch_state(secrets.HA_PLANT_TEMPERATURE_SENSOR)
        self.details["conductivity"] = fetch_state(secrets.HA_PLANT_CONDUCTIVITY_SENSOR)
        print(self.details)

    def display_state(self):
        # Clear the display
        display.set_pen(WHITE)
        display.clear()

        # Display image
        jpeg.open_file("/images/plant.jpg")
        jpeg.decode(0, 0)

        # Draw the page header
        display.set_pen(BLACK)
        display.rectangle(0, 0, WIDTH, 20)

        # Write text in header
        display.set_font("bitmap6")
        display.set_pen(WHITE)
        display.text(self.get_plant_attribute("friendly_name"), 3, 4)

        display.set_pen(BLACK)
        display.text("H", LINE_START_OFFSET, 30)
        display.text("T", LINE_START_OFFSET, 55)
        display.text("C", LINE_START_OFFSET, 80)
        display.text("L", LINE_START_OFFSET, 105)

        display.set_font("bitmap8")
        display.text(self.get_plant_status("moisture"), STATUS_VALUE_OFFSET, 30)
        display.text(self.get_plant_status("temperature"), STATUS_VALUE_OFFSET, 55)
        display.text(self.get_plant_status("conductivity"), STATUS_VALUE_OFFSET, 80)
        display.text(self.get_plant_status("illuminance"), STATUS_VALUE_OFFSET, 105)

        display.update()


plant = HAPlant()
plant.fetch_states()
plant.display_state()

rtc.set_timer(secrets.REFRESH_INTERVAL_MINUTES, ttp=PCF85063A.TIMER_TICK_1_OVER_60HZ)

# Call halt in a loop, on battery this switches off power.
# On USB, the app will exit when A+C is pressed because the launcher picks that up.
while True:
    display.halt()
