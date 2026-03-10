import time
from machine import I2C
from pcf85263a import PCF85263A

def test_alarms():
    print("Initializing I2C...")
    try:
        i2c = I2C(0)
    except Exception as e:
        raise RuntimeError(f"Failed to init I2C(0): {e}")

    rtc = PCF85263A(i2c)
    assert rtc.stopwatch_mode is False, "RTC should start in normal mode, not stopwatch mode"    
    # rtc.software_reset()

    # Preemptively disable alarms and clear flags
    rtc.disable_alarm1()
    rtc.disable_alarm2()

    # Set clock to 57 seconds
    dt = (2024, 12, 31, 23, 59, 57, 2, 0)
    rtc.datetime = dt
    
    # Configure Alarm 1 for exactly 59 seconds (2 seconds from now) with INTA
    print("Setting Alarm 1 for 59 seconds (with INTA)...")
    rtc.set_alarm1(second=59)
    rtc.alarm1_inta_enabled = True
    # Check that reading it back works and only seconds are set
    a1_cfg = rtc.alarm1
    assert a1_cfg == (59, None, None, None, None), f"Alarm 1 config mismatch: {a1_cfg}"
    assert rtc.alarm1_inta_enabled, "INTA not enabled for Alarm 1"
    
    # Configure Alarm 2 for minute 0 (3 seconds from now when rollover happens to 00:00:00) with INTB
    print("Setting Alarm 2 for 0 minutes (with INTB)...")
    rtc.set_alarm2(minute=0)
    rtc.alarm2_intb_enabled = True
    # Check that reading it back works and only minutes are set
    a2_cfg = rtc.alarm2
    assert a2_cfg == (0, None, None), f"Alarm 2 config mismatch: {a2_cfg}"
    assert rtc.alarm2_intb_enabled, "INTB not enabled for Alarm 2"

    # Ensure flags are low
    assert not rtc.alarm1_triggered, "Alarm 1 triggered prematurely!"
    assert not rtc.alarm2_triggered, "Alarm 2 triggered prematurely!"

    assert rtc.stopped is False, "RTC should be in running state"

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

def test_alarms_interrupts():
    print("Initializing I2C for interrupts test...")
    try:
        from machine import Pin
        i2c = I2C(0)
        # Using arbitrary pins D8 and D9 assuming a board like Nano ESP32 or similar is connected
        # with INTA connected to D8 and INTB connected to D9
        interrupt_pin_a = Pin("D8", Pin.IN)
        interrupt_pin_b = Pin("D9", Pin.IN)
    except Exception as e:
        print(f"Skipping interrupt tests: hardware setup not fully available ({e})")
        return

    rtc = PCF85263A(i2c)
    assert rtc.stopwatch_mode is False, "RTC should start in normal mode, not stopwatch mode"
    assert rtc.stopped is False, "RTC should be in running state"
    
    # Preemptively disable alarms and clear flags
    rtc.disable_alarm1()
    rtc.disable_alarm2()

    # Set clock to 57 seconds
    rtc.datetime = (2024, 12, 31, 23, 59, 57, 2, 0)
    
    # State tracker for interrupts
    state = {'a1': False, 'a2': False}

    def on_alarm1(pin):
        state['a1'] = True

    def on_alarm2(pin):
        state['a2'] = True
        
    interrupt_pin_a.irq(trigger=Pin.IRQ_FALLING, handler=on_alarm1)
    interrupt_pin_b.irq(trigger=Pin.IRQ_FALLING, handler=on_alarm2)

    # Configure Alarm 1 and Alarm 2
    rtc.set_alarm1(second=58) # triggers in 1 second
    rtc.alarm1_inta_enabled = True

    rtc.set_alarm2(minute=0) # triggers in 3 seconds at midnight
    rtc.alarm2_intb_enabled = True

    print("Waiting 4 seconds for hardware interrupts to fire...")
    time.sleep(4)

    assert state['a1'], "Hardware interrupt for Alarm 1 (INTA/D8) failed to trigger"
    assert state['a2'], "Hardware interrupt for Alarm 2 (INTB/D9) failed to trigger"

    print("Disabling alarms...")
    rtc.disable_alarm1()
    rtc.disable_alarm2()

    # Disable IRQs
    interrupt_pin_a.irq(handler=None)
    interrupt_pin_b.irq(handler=None)
    
    print("✅ Alarm interrupts test passed!")

if __name__ == "__main__":
    test_alarms()
    test_alarms_interrupts()
