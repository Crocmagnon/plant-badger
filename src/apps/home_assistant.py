import badger2040w as badger2040
from badger2040w import WIDTH
import urequests
from secrets import HA_BASE_URL, HA_ACCESS_TOKEN


display = badger2040.Badger2040W()
display.led(128)
display.set_update_speed(2)

display.connect()


class HAError(Exception):
    pass


class HAFetchStateError(HAError):
    pass


class HAPlant:
    def __init__(self, entity_id):
        self.entity_id = entity_id
        self.state = None
        self._last_fetched = None

    def fetch_state(self) -> None:
        """Fetch state and store in self.state."""
        headers = {
            "Authorization": f"Bearer {HA_ACCESS_TOKEN}",
            "content-type": "application/json",
        }
        url = f"{HA_BASE_URL}/states/{self.entity_id}"
        print("Fetching state from", url)
        res = urequests.get(url, headers=headers)
        if res.status_code != 200:
            msg = f"Error fetching state for {self.entity_id}: {res.text}"
            raise HAFetchStateError(msg)
        data = res.json()
        self.state = data
        res.close()

    def display_state(self):
        print(self.state)


def draw_page(plant):
    print("Drawing page...")
    # Clear the display
    display.set_pen(15)
    display.clear()
    display.set_pen(0)

    # Draw the page header
    display.set_font("bitmap6")
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 20)
    display.set_pen(15)
    display.text("Weather", 3, 4)
    display.set_pen(0)

    display.set_font("bitmap8")
    display.set_pen(0)
    display.rectangle(0, 60, WIDTH, 25)
    display.set_pen(15)
    display.text(
        "Found state, check logs",
        5,
        65,
        WIDTH,
        1,
    )

    display.update()
    plant.display_state()


plant = HAPlant("plant.aloe_vera")
plant.fetch_state()
draw_page(plant)

# Call halt in a loop, on battery this switches off power.
# On USB, the app will exit when A+C is pressed because the launcher picks that up.
while True:
    display.halt()
