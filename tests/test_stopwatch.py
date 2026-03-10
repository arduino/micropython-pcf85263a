import time
from machine import I2C

try:
    from pcf85263a import PCF85263A
except ImportError:
    from pcf85263a import PCF85263A

def elapsed_time_in_hundredths(t_tuple):
    h, m, s, hs = t_tuple
    return h * 360000 + m * 6000 + s * 100 + hs

def test_stopwatch_mode():
    print("Initializing I2C...")
    try:
        i2c = I2C(0)
    except Exception as e:
        raise RuntimeError(f"Failed to init I2C(0): {e}")

    rtc = PCF85263A(i2c)

    # Set to stopwatch mode
    print("Setting to stopwatch mode...")
    rtc.stopwatch_mode = True
    assert rtc.stopwatch_mode is True, "API didn't return True for stopwatch_mode"
    
    # Assert that it stopped automatically
    assert rtc.stopped, "Failed to stop when entering stopwatch mode"

    # Test reset function
    print("Testing stopwatch reset...")
    rtc.stopwatch_reset()
    assert rtc.stopped, "Failed to stop when resetting stopwatch"
    reset_time = rtc.stopwatch_time
    assert reset_time == (0, 0, 0, 0), f"Failed to reset to 0: got {reset_time}"

    # Set initial stopwatch time manually
    expect_time = (10, 5, 30, 50) # 10 hours, 5 mins, 30 secs, 50 hundredths
    print(f"Setting stopwatch time manually to {expect_time}...")
    rtc.stopwatch_time = expect_time
    
    # Assert it didn't start automatically
    assert rtc.stopped, "Failed to remain stopped when setting stopwatch time"

    # Ensure it's correctly set
    set_time = rtc.stopwatch_time
    assert set_time == expect_time, f"Failed to set initial time. Expected {expect_time}, got {set_time}"

    # Explicitly start the stopwatch
    print("Running stopwatch for 2.5 seconds...")
    rtc.start()
    assert not rtc.stopped, "Failed to start the stopwatch"

    # Run for a few seconds
    time.sleep(2.5)

    rtc.stop()
    assert rtc.stopped, "Failed to stop the stopwatch"

    # Read back the stopwatch time
    end_time = rtc.stopwatch_time
    print(f"Read back stopwatch time: {end_time}")
    
    # Calculate elapsed time difference
    start_hs = elapsed_time_in_hundredths(expect_time)
    end_hs = elapsed_time_in_hundredths(end_time)
    diff_hs = end_hs - start_hs
    
    print(f"Elapsed difference in hundredths: {diff_hs}")
    
    # We slept for ~2.5s = 250 hundredths. Allow some tolerance due to sleep execution and I2C overhead time 
    assert 220 <= diff_hs <= 280, f"Elapsed time out of expected bounds: got {diff_hs} hundredths"

    # Return to RTC mode
    print("Returning to RTC mode...")
    rtc.stopwatch_mode = False
    assert rtc.stopwatch_mode is False, "API didn't return False for stopwatch_mode"
    
    print("✅ Stopwatch test passed!")

def test_stopwatch_alarms():
    print("Initializing I2C for stopwatch alarms test...")
    try:
        i2c = I2C(0)
    except Exception as e:
        raise RuntimeError(f"Failed to init I2C(0): {e}")

    rtc = PCF85263A(i2c)
    rtc.stopwatch_mode = True

    print("Testing stopwatch Alarm 1...")
    rtc.set_stopwatch_alarm1(hour=999999, minute=59, second=59)
    a1_cfg = rtc.stopwatch_alarm1
    assert a1_cfg == (999999, 59, 59), f"Stopwatch Alarm 1 config mismatch: {a1_cfg}"

    rtc.set_stopwatch_alarm1(second=15)
    a1_cfg = rtc.stopwatch_alarm1
    assert a1_cfg == (None, None, 15), f"Stopwatch Alarm 1 wildcard mismatch: {a1_cfg}"

    print("Testing stopwatch Alarm 2...")
    rtc.set_stopwatch_alarm2(hour=9999, minute=42)
    a2_cfg = rtc.stopwatch_alarm2
    assert a2_cfg == (9999, 42), f"Stopwatch Alarm 2 config mismatch: {a2_cfg}"

    rtc.set_stopwatch_alarm2(hour=123)
    a2_cfg = rtc.stopwatch_alarm2
    assert a2_cfg == (123, None), f"Stopwatch Alarm 2 wildcard mismatch: {a2_cfg}"

    print("Testing if Alarm 1 triggers...")
    rtc.stopwatch_reset()
    rtc.set_stopwatch_alarm1(hour=0, minute=0, second=2)
    rtc.start()
    
    time.sleep(2.5)
    
    assert rtc.alarm1_triggered, "Alarm 1 didn't trigger in stopwatch mode!"
    rtc.stop()

    rtc.stopwatch_mode = False
    print("✅ Stopwatch alarms test passed!")

if __name__ == "__main__":
    test_stopwatch_mode()
    test_stopwatch_alarms()

