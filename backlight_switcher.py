import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By


GECKODRIVER = "C:/Scheduler/geckodriver.exe"
SCHEDULE = "C:/Scheduler/sun.txt"
ADDRESS_FILENAME = "C:/Users/ecue/Desktop/ActionPad2_address.txt"
WAIT_PAGE_LOADING_SEC = 5

pad_state: set[str] = None
next_sun_event = {
    'timestamp': None,
    'sun_direction': None,
}


def activate():
    while True:
        with webdriver.Firefox(executable_path=GECKODRIVER) as driver:
            driver.get(get_address_from_file(ADDRESS_FILENAME))
            time.sleep(WAIT_PAGE_LOADING_SEC)
            setpad_state(driver)
            setnext_sun_event()
            direction = next_sun_event['sun_direction']
            if (direction == "sunrise") and check("is_all_off"):
                turn_on(driver)
            elif (direction == "sunset") and check("is_something_on"):
                turn_off(driver)
            driver.quit()
            sun_event_dt = datetime.fromtimestamp(next_sun_event['timestamp']).strftime("%m/%d/%Y, %H:%M:%S")
            print("next sun event datetime: " + sun_event_dt)
            print("next sun event direction: " + next_sun_event['sun_direction'])
        sleep()


def get_address_from_file(address: str):
    with open(address) as address_file:
        return address_file.readlines()[0]


def setpad_state(driver):
    global pad_state
    pad_state = set()
    buttons = driver.find_elements(By.TAG_NAME, "span")
    for btn in buttons:
        try:
            pad_state.add(btn.text)
        except:
            continue


def setnext_sun_event(_now: datetime = None):
    
    now = datetime.now() if _now is None else _now
    tomorrow = now + timedelta(days=1)

    schedule = get_schedule_at_day(int(now.day), int(now.month))
    schedule_tomorrow = get_schedule_at_day(int(tomorrow.day), int(tomorrow.month))

    upcoming_events = [time_to_timestamp(schedule['sunrise'], now), \
                       time_to_timestamp(schedule['sunset'], now), \
                       time_to_timestamp(schedule_tomorrow['sunrise'], tomorrow), \
                       time_to_timestamp(schedule_tomorrow['sunset'], tomorrow)]

    next_sun_event['timestamp'] = get_sun_event(now, upcoming_events)
    next_sun_event['sun_direction'] = get_sun_direction(now, upcoming_events)
    

def get_sun_event(now: datetime, events) -> float:
    for event in events:
        if now.timestamp() < event:
            return event
    raise Exception("get_sun_event() is failed\n" \
                    + f"now = {now}\n" \
                    + f"now.timestamp() = {now.timestamp()}\n"
                    + f"events[0] = {events[0]}\n" \
                    + f"events[1] = {events[1]}\n" \
                    + f"events[2] = {events[2]}\n" \
                    + f"events[3] = {events[3]}\n")


def get_sun_direction(now: datetime, events) -> str:
    if now.timestamp() < events[0]:
        return 'sunrise'
    if now.timestamp() < events[1]:
        return 'sunset'
    if now.timestamp() < events[2]:
        return 'sunrise'
    if now.timestamp() < events[3]:
        return 'sunset'
    raise Exception("get_sun_direction() is failed\n" \
                    + f"now = {now}\n" \
                    + f"now.timestamp() = {now.timestamp()}\n"
                    + f"events[0] = {events[0]}\n" \
                    + f"events[1] = {events[1]}\n" \
                    + f"events[2] = {events[2]}\n" \
                    + f"events[3] = {events[3]}\n")
    

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


def sleep(is_test: bool = False):
    sun_event = next_sun_event['timestamp']
    now = datetime.now().timestamp()
    seconds_to_wake_up = sun_event - now
    print("app sleeps: " + str(seconds_to_wake_up) + " seconds.")
    print("awake datetime: " + datetime.fromtimestamp(now + seconds_to_wake_up).strftime("%m/%d/%Y, %H:%M:%S"))
    if not is_test:
        time.sleep(seconds_to_wake_up)


# day_dot_month[0] == day at month
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


def time_to_datetime(t: str, now = datetime.now()):
    """t: 'hh:mm'"""
    t = t.replace("\n", '')
    hours = int(t.split(':')[0])
    minutes = int(t.split(':')[1])
    return datetime(now.year,
                    now.month,
                    now.day,
                    hours,
                    minutes)


def time_to_timestamp(t: str, now = datetime.now()):
    return time_to_datetime(t, now).timestamp()


def test():
    test_times = []
    now = datetime.now()

    test_times.append(datetime(now.year, 1, 1, 0, 0))
    test_times.append(datetime(now.year, 6, 15, 18, 0))
    test_times.append(datetime(now.year, 5, 31, 4, 16))
    test_times.append(datetime(now.year, 5, 31, 4, 17))
    test_times.append(datetime(now.year, 5, 31, 4, 18))
    test_times.append(datetime(now.year, 5, 31, 21, 46))
    test_times.append(datetime(now.year, 5, 31, 21, 47))
    test_times.append(datetime(now.year, 5, 31, 21, 48))
    test_times.append(datetime(now.year, 12, 31, 23, 59))
    test_times.append(datetime(now.year, 5, 15, 3, 59))
    test_times.append(datetime(now.year, 5, 15, 6, 59))
    test_times.append(datetime(now.year, 5, 15, 21, 59))
    test_times.append(datetime(now.year, 5, 16, 8, 0))
    
    with webdriver.Firefox(executable_path=GECKODRIVER) as driver:
        driver.get(get_address_from_file(ADDRESS_FILENAME))
        time.sleep(WAIT_PAGE_LOADING_SEC)
        
        for test_time in test_times:
            setpad_state(driver)
            print(f"---> test for {test_time}:")
            setnext_sun_event(test_time)
            direction = next_sun_event['sun_direction']
            if (direction == 'sunrise') and check("is_all_off"):
                turn_on(driver)
                print("off")
            elif (direction == 'sunset') and check("is_something_on"):
                turn_off(driver)
                print("on")
            sun_event_dt = datetime.fromtimestamp(next_sun_event['timestamp']).strftime("%m/%d/%Y, %H:%M:%S")
            print("next sun event datetime: " + sun_event_dt)
            print("next sun event direction: " + next_sun_event['sun_direction'])
            sleep(is_test = True)
        driver.quit()


def test2():
    while True:
        with webdriver.Firefox(executable_path=GECKODRIVER) as driver:
            driver.get(get_address_from_file(ADDRESS_FILENAME))
            time.sleep(WAIT_PAGE_LOADING_SEC)
            setpad_state(driver)
            setnext_sun_event()         
            direction = next_sun_event['sun_direction']
            if (direction == "sunrise") and check("is_all_off"):
                turn_on(driver)
            elif (direction == "sunset") and check("is_something_on"):
                turn_off(driver)
            driver.quit()
            sun_event_dt = datetime.fromtimestamp(next_sun_event['timestamp']).strftime("%m/%d/%Y, %H:%M:%S")
            print("next sun event datetime: " + sun_event_dt)
            print("next sun event direction: " + next_sun_event['sun_direction'])
        sleep()


#test()
#test2()
activate()
