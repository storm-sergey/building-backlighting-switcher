import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

GECKODRIVER = "C:/.../geckodriver.exe"
SCHEDULE = "C:/.../sun.txt"
ADDRESS = "http://..."


class LightBySchedule:
    def __init__(self):
        self._pad_state: set[str] = None
        self._next_sun_event = {
            'datetime': None,
            'sun_direction': None,
        }

    def activate(self):
        while True:
            with webdriver.Firefox(executable_path=GECKODRIVER) as driver:
                driver.get(ADDRESS)
                time.sleep(10)
                self._set_pad_state(driver)
                self._set_next_sun_event()
                direction = self._next_sun_event['sun_direction']
                if (direction == "sunrise") and self._check("is_all_off"):
                    self._turn_on(driver)
                elif (direction == "sunset") and self._check("is_something_on"):
                    self._turn_off(driver)
                driver.quit()
                sun_event_dt = datetime.fromtimestamp(self._next_sun_event['datetime']).strftime("%m/%d/%Y, %H:%M:%S")
                print("next sun event datetime: " + sun_event_dt)
                print("next sun event direction: " + self._next_sun_event['sun_direction'])
            self._sleep()

    def _set_pad_state(self, driver):
        self._pad_state = set()
        buttons = driver.find_elements(By.TAG_NAME, "span")
        for btn in buttons:
            try:
                self._pad_state.add(btn.text)
            except:
                continue

    def _set_next_sun_event(self):
        now = datetime.now()
        schedule = self.get_schedule_at_day(int(now.day))
        sunrise_dt = self.time_to_datetime(schedule['sunrise'])
        sunset_dt = self.time_to_datetime(schedule['sunset'])
        if now.timestamp() > sunset_dt:
            schedule = self.get_schedule_at_day(int(now.day) + 1)
            self._next_sun_event['datetime'] = self.time_to_datetime(schedule['sunrise'], is_next_day = True)
            self._next_sun_event['sun_direction'] = 'sunrise'
        else:
            self._next_sun_event['datetime'] = sunrise_dt if (now.timestamp() < sunrise_dt) else sunset_dt
            self._next_sun_event['sun_direction'] = 'sunrise' if (now.timestamp() < sunrise_dt) else 'sunset'
            

    def _check(self, mode):
        modes = {
            "is_something_on": False,
            "is_all_off": True
        }
        if "Все вkл./выkл." in self._pad_state:
            return modes[mode]
        for btn in self._pad_state:
            if btn.endswith("вкл."):
                return not modes[mode]
        return modes[mode]

    def _turn_on(self, driver):
        if "Все вkл./выkл." in self._pad_state:
            self._click(driver, "Все вkл./выkл.")
        self._click(driver, "Все выкл.")

    def _turn_off(self, driver):
        for btn in self._pad_state:
            if btn.endswith("вкл."):
                self._click(driver, btn)

    def _click(self, driver, btn_name):
        buttons = driver.find_elements(By.TAG_NAME, "span")
        for btn in buttons:
            try:
                if btn.text == btn_name:
                    btn.click()
                    break
            except:
                continue

    def _sleep(self):
        sun_event = self._next_sun_event['datetime']
        now = datetime.now().timestamp()
        seconds_to_wake_up = sun_event - now
        print("app sleeps: " + str(seconds_to_wake_up) + " seconds.")
        print("awake datetime: " + datetime.fromtimestamp(now + seconds_to_wake_up).strftime("%m/%d/%Y, %H:%M:%S"))
        time.sleep(seconds_to_wake_up)

    # schedule_at_line[0] == day at month
    # schedule_at_line[1] == sunrise time
    # schedule_at_line[2] == sunset time
    def get_schedule_at_day(self, day: int):
        with open(SCHEDULE) as sun_schedule:
            lines = sun_schedule.readlines()
            for line in lines:
                schedule_at_line = line.split(" ")
                if int(schedule_at_line[0]) == day:
                    return {
                        "day": schedule_at_line[0],
                        "sunrise": schedule_at_line[1],
                        "sunset": schedule_at_line[2]
                    }

    def time_to_datetime(self, t: str, is_next_day:bool = False):
        """t: 'hh:mm'"""
        t = t.replace("\n", '')
        hours = int(t.split(':')[0])
        minutes = int(t.split(':')[1])
        now = datetime.now()
        return (datetime(now.year,
                         now.month,
                         now.day + 1 if is_next_day else now.day,
                         hours,
                         minutes)).timestamp()


if __name__ == '__main__':
    LightBySchedule().activate()
