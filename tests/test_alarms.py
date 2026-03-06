import time
from machine import I2C

try:
    from pcf85263 import PCF85263
except ImportError:
    from pcf85263 import PCF85263

def test_alarms():
    print("Initializing I2C...")
    try:
        i2c = I2C(0)
    except Exception as e:
        raise RuntimeError(f"Failed to init I2C(0): {e}")

    rtc = PCF85263(i2c)
    
    # Preemptively disable alarms and clear flags
    rtc.disable_alarm1()
    rtc.disable_alarm2()

    # Set clock to 57 seconds
    dt = (2024, 12, 31, 23, 59, 57, 2, 0)
    rtc.datetime = dt
    
    # Configure Alarm 1 for exactly 59 seconds (2 seconds from now) with INTA
    print("Setting Alarm 1 for 59 seconds (with INTA)...")
    rtc.set_alarm1(seconds=59)
    rtc.alarm1_inta_enabled = True
    # Check that reading it back works and only seconds are set
    a1_cfg = rtc.alarm1
    assert a1_cfg == (59, None, None, None, None), f"Alarm 1 config mismatch: {a1_cfg}"
    assert rtc.alarm1_inta_enabled, "INTA not enabled for Alarm 1"
    
    # Configure Alarm 2 for minute 0 (3 seconds from now when rollover happens to 00:00:00) with INTB
    print("Setting Alarm 2 for 0 minutes (with INTB)...")
    rtc.set_alarm2(minutes=0)
    rtc.alarm2_intb_enabled = True
    # Check that reading it back works and only minutes are set
    a2_cfg = rtc.alarm2
    assert a2_cfg == (0, None, None), f"Alarm 2 config mismatch: {a2_cfg}"
    assert rtc.alarm2_intb_enabled, "INTB not enabled for Alarm 2"

    # Ensure flags are low
    assert not rtc.alarm1_triggered, "Alarm 1 triggered prematurely!"
    assert not rtc.alarm2_triggered, "Alarm 2 triggered prematurely!"

    print("Waiting 3 seconds for alarms to trigger...")
    time.sleep(3)
    
    # Check flags
    a1_triggered = rtc.alarm1_triggered
    
    # Since we slept for 3 seconds, it should be 23:59:00 meaning both triggers
    assert a1_triggered, "Alarm 1 did not trigger as expected"
    
    # Assert that reading the property cleared the flag automatically
    assert not rtc.alarm1_triggered, "Alarm 1 flag did not auto-clear"
    
    # To catch rollover time variations for Alarm 2, sleep 1 more sec just in case, though it should have triggered
    time.sleep(1)
    a2_triggered = rtc.alarm2_triggered
    assert a2_triggered, "Alarm 2 did not trigger as expected during rollover"
    assert not rtc.alarm2_triggered, "Alarm 2 flag did not auto-clear"
    
    print("Disabling alarms...")
    rtc.disable_alarm1()
    rtc.disable_alarm2()
    
    assert not rtc.alarm1_triggered, "Disable failed for Alarm 1"
    assert not rtc.alarm2_triggered, "Disable failed for Alarm 2"
    
    # Ensure interrupts are disabled
    assert not rtc.alarm1_inta_enabled, "INTA not disabled for Alarm 1"
    assert not rtc.alarm2_intb_enabled, "INTB not disabled for Alarm 2"
    
    print("✅ Alarms test passed!")

if __name__ == "__main__":
    test_alarms()
