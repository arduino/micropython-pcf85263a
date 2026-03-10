"""
Example showing how to configure and handle hardware interrupts 
from the PCF85263A RTC alarms using the INTA and INTB pins.

Initial author: Sebastian Romero (s.romero@arduino.cc)
Copyright (C) Arduino s.r.l. and/or its affiliated companies
"""

from machine import I2C, Pin
import time
from pcf85263a import PCF85263A

# Initialize I2C - adjust depending on your board
i2c = I2C(0)
interrupt_pin_a = Pin("D8", Pin.IN) # Example pin for INTA
interrupt_pin_b = Pin("D9", Pin.IN) # Example pin for INTB

# Create RTC instance
rtc = PCF85263A(i2c)

# Set the current time to slightly before the alarm goes off
# (2024, 12, 31, 23, 59, 50, 2, 0) -> Year, Month, Day, Hour, Minute, Second, Weekday, Yearday
rtc.datetime = (2024, 12, 31, 23, 59, 50, 2, 0)
print("Current time set to 23:59:50")

# Set Alarm 1 to trigger at exactly 23:59:55
print("Setting Alarm 1 for 23:59:55 (matches exactly 55 seconds)...")
rtc.set_alarm1(second=55)
rtc.alarm1_inta_enabled = True

# Set Alarm 2 to trigger when minutes roll over to 0 (midnight)
print("Setting Alarm 2 for minute 0 (midnight rollover)...")
rtc.set_alarm2(minute=0)
rtc.alarm2_intb_enabled = True

alarm1_fired = False
alarm2_fired = False

def on_alarm1_interrupt(pin):
    global alarm1_fired
    alarm1_fired = True

def on_alarm2_interrupt(pin):
    global alarm2_fired
    alarm2_fired = True

interrupt_pin_a.irq(trigger=Pin.IRQ_FALLING, handler=on_alarm1_interrupt)
interrupt_pin_b.irq(trigger=Pin.IRQ_FALLING, handler=on_alarm2_interrupt)

print("Waiting for alarms to trigger...")
try:
    while True:
        # Check alarm 1 interrupt software flag
        if alarm1_fired:
            alarm1_fired = False
            print("⏰ Alarm 1 Interrupt Triggered!")
            rtc.clear_alarm1_flag() # Clear the hardware flag for Alarm 1
            rtc.disable_alarm1() # Disable Alarm 1 to prevent retriggering
            dt = rtc.datetime
            print(f"Time is now {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")
        
        # Check alarm 2 interrupt software flag
        if alarm2_fired:
            alarm2_fired = False
            print("⏰ Alarm 2 Interrupt Triggered!")
            rtc.clear_alarm2_flag() # Clear the hardware flag for Alarm 2
            rtc.disable_alarm2() # Completely disable Alarm 2
            dt = rtc.datetime
            print(f"Time is now {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")
            break # Exit after alarm 2 triggers
            
        time.sleep(0.1) # Short nap to yield to other processes without missing software flags
except KeyboardInterrupt:
    print("Exiting...")
