"""
Example script to test the PCF85263 RTC using MicroPython and mpremote.

Initial author: Sebastian Romero (s.romero@arduino.cc)
Copyright (C) Arduino s.r.l. and/or its affiliated companies
"""

from machine import I2C, Pin
import time

try:
    # Try importing from src if running locally
    from pcf85263 import PCF85263
except ImportError:
    # If installed via mip, it will be in the system path
    from pcf85263 import PCF85263

def test_availability(i2c):
    print("Scanning I2C bus...")
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C devices found.")
    print("Found devices at addresses:", [hex(d) for d in devices])

def test_set_and_get_datetime(rtc, test_dt):
    # Tuple: (year, month, mday, hour, minute, second, weekday, yearday)
    print(f"Setting datetime to {test_dt}")
    rtc.datetime = test_dt

    # Read back immediately
    read_dt = rtc.datetime
    print(f"Read back datetime: {read_dt}")

    # Check if the year is still the same
    if read_dt[0] != test_dt[0]:
        raise RuntimeError(f"Year has changed! Expected: {test_dt[0]}, Got: {read_dt[0]}")

    # Check if the month is still the same
    if read_dt[1] != test_dt[1]:
        raise RuntimeError(f"Month has changed! Expected: {test_dt[1]}, Got: {read_dt[1]}")

    # Check if the day is still the same
    if read_dt[2] != test_dt[2]:
        raise RuntimeError(f"Day has changed! Expected: {test_dt[2]}, Got: {read_dt[2]}")

    # Check if the hour is still the same
    if read_dt[3] != test_dt[3]:
        raise RuntimeError(f"Hour has changed! Expected: {test_dt[3]}, Got: {read_dt[3]}")

    # Check if the minute is still the same
    if read_dt[4] != test_dt[4]:
        raise RuntimeError(f"Minute has changed! Expected: {test_dt[4]}, Got: {read_dt[4]}")

    # Check if the second is still the same
    if read_dt[5] != test_dt[5]:
        raise RuntimeError(f"Second has changed! Expected: {test_dt[5]}, Got: {read_dt[5]}")

    # Check if the weekday is still the same
    if read_dt[6] != test_dt[6]:
        raise RuntimeError(f"Weekday has changed! Expected: {test_dt[6]}, Got: {read_dt[6]}")

def test_ticking(rtc, test_dt):
    # Wait to see if the clock is ticking
    print("Waiting 2 seconds for clock to tick...")
    time.sleep(2)
    tick_dt = rtc.datetime
    print(f"Datetime after 2 seconds: {tick_dt}")

    # Ensure the second has increased
    if tick_dt[5] <= test_dt[5]:
        raise RuntimeError(f"Second has not increased! Expected: >{test_dt[5]}, Got: {tick_dt[5]}")

def test_rollover(rtc, test_dt):
    # Wait to see month/day rollover if we wait long enough: 50 + 12 = 62s
    print("Waiting 10 seconds for rollover...")
    time.sleep(10)
    rollover_dt = rtc.datetime
    print(f"Datetime after rollover: {rollover_dt}")

    # Ensure the minute has rolled over
    if rollover_dt[4] != (test_dt[4] + 1) % 60:
        raise RuntimeError(f"Minute has not rolled over! Expected: {(test_dt[4] + 1) % 60}, Got: {rollover_dt[4]}")

    # Ensure the day has rolled over
    if rollover_dt[2] != (test_dt[2] + 1) % 31:
        raise RuntimeError(f"Day has not rolled over! Expected: {(test_dt[2] + 1) % 31}, Got: {rollover_dt[2]}")

    # Ensure the month has rolled over
    if rollover_dt[1] != (test_dt[1] + 1) % 12:
        raise RuntimeError(f"Month has not rolled over! Expected: {(test_dt[1] + 1) % 12}, Got: {rollover_dt[1]}")

    # Ensure the year has rolled over
    if rollover_dt[0] != test_dt[0] + 1:
        raise RuntimeError(f"Year has not rolled over! Expected: {test_dt[0] + 1}, Got: {rollover_dt[0]}")

def test_mktime_localtime(rtc, test_dt):
    print("Testing time.mktime and time.localtime compatibility...")
    try:
        # MicroPython's time epoch is typically 2000-01-01. Our tuple uses 2-digit years.
        # We need to map our 2-digit year back to a 4-digit year for time module compatibility.
        # dt format from rtc: (year, month, mday, hour, minute, second, weekday, yearday)
        y, mo, d, h, mi, s, wd, yd = test_dt
        full_dt = (y, mo, d, h, mi, s, wd, yd)
        
        timestamp = time.mktime(full_dt)
        print(f"mktime(full_dt) result: {timestamp}")
        
        local_dt = time.localtime(timestamp)
        print(f"localtime(timestamp) result: {local_dt}")
        
        # Verify the key fields match (excluding yearday and weekday which localtime may calculate differently)
        if local_dt[0:6] == full_dt[0:6]:
            print("Time conversion check passed!")
        else:
            raise RuntimeError("Time conversion mismatch between mktime and localtime.")
            
    except Exception as e:
        raise RuntimeError(f"Time conversion test failed with error: {e}")
    

def run_tests():
    # Adjust I2C pins based on your specific board if necessary.
    # Defaulting to typically used hardware I2C on many boards, or specific pins:
    try:
        print("Initializing I2C...")
        i2c = I2C(0)
    except Exception as e:
        raise RuntimeError(f"Failed to init I2C(0): {e}. Fallback to SoftI2C usually requires explicit pins.")
    
    test_availability(i2c)

    try:
        rtc = PCF85263(i2c)
        print("PCF85263 initialized successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize PCF85263: {e}")

    test_dt = (2024, 12, 31, 23, 59, 50, 2, 0)
    test_set_and_get_datetime(rtc, test_dt)
    test_ticking(rtc, test_dt)
    test_rollover(rtc, test_dt)
    test_mktime_localtime(rtc, test_dt)
        
    print("✅ Tests completed successfully!")

if __name__ == "__main__":
    run_tests()
