import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By


GECKODRIVER = "C:/Scheduler/geckodriver.exe"
SCHEDULE = "C:/Scheduler/sun_new.txt"
ADDRESS = "http://192.168.123.99:8081/ActionPad2/ActionPad2.html?idx=1"
WAIT_PAGE_LOADING_SEC = 10


pad_state: set[str] = None
next_sun_event = {
    'datetime': None,
    'sun_direction': None,
}


def activate():
    while True:
        with webdriver.Firefox(executable_path=GECKODRIVER) as driver:
            driver.get(ADDRESS)
            time.sleep(WAIT_PAGE_LOADING_SEC)
            setpad_state(driver)
            setnext_sun_event()
            direction = next_sun_event['sun_direction']
            if (direction == "sunrise") and check("is_all_off"):
                turn_on(driver)
            elif (direction == "sunset") and check("is_something_on"):
                turn_off(driver)
            driver.quit()
            sun_event_dt = datetime.fromtimestamp(next_sun_event['datetime']).strftime("%m/%d/%Y, %H:%M:%S")
            print("next sun event datetime: " + sun_event_dt)
            print("next sun event direction: " + next_sun_event['sun_direction'])
        sleep()


def setpad_state(driver):
    global pad_state
    pad_state = set()
    buttons = driver.find_elements(By.TAG_NAME, "span")
    for btn in buttons:
        try:
            pad_state.add(btn.text)
        except:
            continue


def setnext_sun_event():
    now = datetime.now()
        schedule = get_schedule_at_day(int(now.day))
        sunrise_dt = time_to_datetime(schedule['sunrise'])
        sunset_dt = time_to_datetime(schedule['sunset'])
        if now.timestamp() > sunset_dt:
            schedule = get_schedule_at_day(int(now.day) + 1)
            next_sun_event['datetime'] = time_to_datetime(schedule['sunrise'], is_next_day = True)
            next_sun_event['sun_direction'] = 'sunrise'
        else:
            next_sun_event['datetime'] = sunrise_dt if (now.timestamp() < sunrise_dt) else sunset_dt
            next_sun_event['sun_direction'] = 'sunrise' if (now.timestamp() < sunrise_dt) else 'sunset'
        

def check(mode):
    modes = {
        "is_something_on": False,
        "is_all_off": True
    }
    if "Все вkл./выkл." in pad_state:
        return modes[mode]
    for btn in pad_state:
        if btn.endswith("вкл."):
            return not modes[mode]
    return modes[mode]


def turn_on(driver):
    if "Все вkл./выkл." in pad_state:
        click(driver, "Все вkл./выkл.")
    click(driver, "Все выкл.")


def turn_off(driver):
    for btn in pad_state:
        if btn.endswith("вкл."):
            click(driver, btn)


def click(driver, btn_name):
    buttons = driver.find_elements(By.TAG_NAME, "span")
    for btn in buttons:
        try:
            if btn.text == btn_name:
                btn.click()
                break
        except:
            continue


def sleep():
    sun_event = next_sun_event['datetime']
    now = datetime.now().timestamp()
    seconds_to_wake_up = sun_event - now
    print("app sleeps: " + str(seconds_to_wake_up) + " seconds.")
    print("awake datetime: " + datetime.fromtimestamp(now + seconds_to_wake_up).strftime("%m/%d/%Y, %H:%M:%S"))
    time.sleep(seconds_to_wake_up)


# schedule_at_line[0] == day at month
# schedule_at_line[1] == sunrise time
# schedule_at_line[2] == sunset time
def get_schedule_at_day(day: int, month: int):
    with open(SCHEDULE) as sun_schedule:
        lines = sun_schedule.readlines()
        schedule_at_line: list[str]
        day_and_month: list[str]
        for line in lines:
            schedule_at_line = line.split(" ")
            day_dot_month = schedule_at_line[0].split(".")
            if int(day_dot_month[0]) == day and \
               int(day_dot_month[1]) == month:
                return {
                    "day": day_dot_month[0],
                    "sunrise": schedule_at_line[1],
                    "sunset": schedule_at_line[2]
                }


def time_to_datetime(t: str, is_next_day:bool = False):
    """t: 'hh:mm'"""
    t = t.replace("\n", '')
    hours = int(t.split(':')[0])
    minutes = int(t.split(':')[1])
    now = datetime.now()
    return datetime(now.year,
                    now.month,
                    now.day + 1 if is_next_day else now.day,
                    hours,
                    minutes)


def time_to_timestamp(t: str, is_next_day:bool = False):
    return time_to_datetime(t, is_next_day).timestamp()


activate()
