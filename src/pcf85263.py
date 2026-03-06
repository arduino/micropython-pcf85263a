"""
MicroPython library for NXP PCF85263 Real-time clock/calendar.

Initial author: Sebastian Romero (s.romero@arduino.cc)
Copyright (C) Arduino s.r.l. and/or its affiliated companies
"""

from machine import I2C
from micropython import const

PCF85263_DEFAULT_ADDRESS = const(0x51)

PCF85263_SECONDS_100TH = const(0x00)
PCF85263_SECONDS = const(0x01)
PCF85263_MINUTES = const(0x02)
PCF85263_HOURS = const(0x03)
PCF85263_DAYS = const(0x04)
PCF85263_WEEKDAYS = const(0x05)
PCF85263_MONTHS = const(0x06)
PCF85263_YEARS = const(0x07)

PCF85263_ALARM1_SECONDS = const(0x08)
PCF85263_ALARM2_MINUTES = const(0x0D)
PCF85263_ALARM_ENABLES = const(0x10)

PCF85263_FUNCTION = const(0x28)
PCF85263_FLAGS = const(0x2B)
PCF85263_STOP_ENABLE = const(0x2E)

class PCF85263:
    """PCF85263 RTC driver class."""

    def __init__(self, i2c=None, address=PCF85263_DEFAULT_ADDRESS):
        """Initializes the driver.
        
        Args:
            i2c: A machine.I2C object. If None, I2C(0) will be used.
            address: The I2C address of the device (defaults to 0x51).
        """
        if i2c is None:
            i2c = I2C(0)
        self.i2c = i2c
        self.address = address
        self._buffer = bytearray(8)
        self._bytebuf = memoryview(self._buffer[0:1])
        
        # Verify device presence
        devices = self.i2c.scan()
        if self.address not in devices:
            raise OSError(f"Device not found at I2C address {hex(self.address)}")

        # Ensure we are in RTC mode (0)
        self._set_rtc_mode()

    def _write_byte(self, reg, val):
        self._bytebuf[0] = val
        self.i2c.writeto_mem(self.address, reg, self._bytebuf)

    def _read_byte(self, reg):
        self.i2c.readfrom_mem_into(self.address, reg, self._bytebuf)
        return self._bytebuf[0]
        
    def _read_registers(self, reg, count):
        buffer = bytearray(count)
        self.i2c.readfrom_mem_into(self.address, reg, buffer)
        return buffer
        
    def _write_registers(self, reg, buffer):
        self.i2c.writeto_mem(self.address, reg, buffer)
        
    def _bcd2dec(self, bcd):
        return (((bcd & 0xF0) >> 4) * 10 + (bcd & 0x0F))

    def _dec2bcd(self, dec):
        tens, units = divmod(dec, 10)
        return (tens << 4) + units
        
    def _set_rtc_mode(self):
        # PCF85263_FUNCTION register
        # mode 0: RTC mode, mode 1: Stopwatch mode
        mask = self._read_byte(PCF85263_FUNCTION)
        mask &= 0xEF  # Clear bit 4 (RTCM)
        mask |= 0x80  # Set bit 7 (100TH) to enable hundredths
        self._write_byte(PCF85263_FUNCTION, mask)

    def _set_stopwatch_mode(self):
        # PCF85263_FUNCTION register
        mask = self._read_byte(PCF85263_FUNCTION)
        mask |= 0x10  # Set bit 4 (RTCM)
        mask |= 0x80  # Set bit 7 (100TH) to enable hundredths
        self._write_byte(PCF85263_FUNCTION, mask)
        
    def stop(self):
        """Stops the entire RTC clock. Note: This is not just for the stopwatch."""
        self._write_byte(PCF85263_STOP_ENABLE, 1)
        
    def start(self):
        """Starts the entire RTC clock. Note: This is not just for the stopwatch."""
        self._write_byte(PCF85263_STOP_ENABLE, 0)
        
    @property
    def stopped(self):
        """Returns True if the RTC clock is stopped, False otherwise."""
        return self._read_byte(PCF85263_STOP_ENABLE) == 1
        
    @property
    def datetime(self):
        """Get or set the current datetime of the RTC.
        
        When reading, returns a tuple: (year, month, mday, hour, minute, second, weekday, yearday)
        When setting, expects a tuple: (year, month, mday, hour, minute, second, weekday, yearday)
        
        Year is 2000-2099.
        Weekday is 0-6 (0=Monday, 6=Sunday as per MicroPython standard).
        yearday is always 0 (not supported by RTC but required for tuple compatibility).
        """
        # Read 7 registers starting from SECONDS (0x01)
        # Sequence: SECONDS, MINUTES, HOURS, DAYS, WEEKDAYS, MONTHS, YEARS
        data = self._read_registers(PCF85263_SECONDS, 7)
        
        seconds = self._bcd2dec(data[0] & 0x7F)
        minutes = self._bcd2dec(data[1] & 0x7F)
        hours = self._bcd2dec(data[2] & 0x3F)
        day = self._bcd2dec(data[3] & 0x3F)   # 0x04 DAYS register (1-31)
        weekday = data[4] & 0x07             # 0x05 WEEKDAYS register (0-6), note: not strictly BCD
        month = self._bcd2dec(data[5] & 0x1F)
        year = self._bcd2dec(data[6] & 0xFF) + 2000 # Include century
        
        return (year, month, day, hours, minutes, seconds, weekday, 0)
        
    @datetime.setter
    def datetime(self, dt):
        year, month, day, hours, minutes, seconds, weekday, yearday = dt
        
        # Validations
        if not (0 <= seconds <= 59): raise ValueError("Seconds out of range [0-59]")
        if not (0 <= minutes <= 59): raise ValueError("Minutes out of range [0-59]")
        if not (0 <= hours <= 23): raise ValueError("Hours out of range [0-23]")
        if not (1 <= day <= 31): raise ValueError("Day out of range [1-31]")
        if not (0 <= weekday <= 6): raise ValueError("Weekday out of range [0-6]")
        if not (1 <= month <= 12): raise ValueError("Month out of range [1-12]")
        if not (2000 <= year <= 2099): raise ValueError("Year out of range [2000-2099]")
        
        buffer = bytearray(7)
        buffer[0] = self._dec2bcd(seconds)
        buffer[1] = self._dec2bcd(minutes)
        buffer[2] = self._dec2bcd(hours)
        buffer[3] = self._dec2bcd(day)
        buffer[4] = weekday # Weekday is generally read as regular number, max 6 anyway
        buffer[5] = self._dec2bcd(month)
        buffer[6] = self._dec2bcd(year - 2000) # Century needs to be removed
        
        self.stop()
        self._write_registers(PCF85263_SECONDS, buffer)
        self.start()

    @property
    def stopwatch_time(self):
        """Get or set the current stopwatch time.
        
        When reading, returns a tuple: (hours, minutes, seconds, hundredths)
        When setting, expects a tuple: (hours, minutes, seconds, hundredths)
        
        Hours is 0-999999.
        Minutes, Seconds is 0-59.
        Hundredths is 0-99.
        """
        # Read 6 registers starting from 100TH SECONDS (0x00)
        data = self._read_registers(PCF85263_SECONDS_100TH, 6)
        
        hundredths = self._bcd2dec(data[0] & 0xFF)
        seconds = self._bcd2dec(data[1] & 0x7F)
        minutes = self._bcd2dec(data[2] & 0x7F)
        hours_L = self._bcd2dec(data[3] & 0xFF)
        hours_M = self._bcd2dec(data[4] & 0xFF)
        hours_H = self._bcd2dec(data[5] & 0xFF)
        
        hours = hours_H * 10000 + hours_M * 100 + hours_L
        return (hours, minutes, seconds, hundredths)

    @stopwatch_time.setter
    def stopwatch_time(self, time_tuple):
        hours, minutes, seconds, hundredths = time_tuple
        
        if not (0 <= hundredths <= 99): raise ValueError("Hundredths out of range [0-99]")
        if not (0 <= seconds <= 59): raise ValueError("Seconds out of range [0-59]")
        if not (0 <= minutes <= 59): raise ValueError("Minutes out of range [0-59]")
        if not (0 <= hours <= 999999): raise ValueError("Hours out of range [0-999999]")
        
        hours_H = hours // 10000
        hours_M = (hours % 10000) // 100
        hours_L = hours % 100
        
        buffer = bytearray(6)
        buffer[0] = self._dec2bcd(hundredths)
        buffer[1] = self._dec2bcd(seconds)
        buffer[2] = self._dec2bcd(minutes)
        buffer[3] = self._dec2bcd(hours_L)
        buffer[4] = self._dec2bcd(hours_M)
        buffer[5] = self._dec2bcd(hours_H)
        
        self.stop()
        self._write_registers(PCF85263_SECONDS_100TH, buffer)

    def stopwatch_reset(self):
        """Resets the stopwatch to 0 and stops it."""
        self.stopwatch_time = (0, 0, 0, 0)

    @property
    def stopwatch_mode(self):
        """Get or set the RTC mode to Real-Time Clock (False) or Stopwatch (True)."""
        mask = self._read_byte(PCF85263_FUNCTION)
        return bool(mask & 0x10)

    @stopwatch_mode.setter
    def stopwatch_mode(self, is_stopwatch):
        if is_stopwatch:
            self.stop()
            self._set_stopwatch_mode()
        else:
            self._set_rtc_mode()
            self.start()

    def set_alarm1(self, seconds=None, minutes=None, hours=None, days=None, months=None):
        """Sets Alarm 1. Passing None acts as a wildcard (ignores that field)."""
        buffer = bytearray(5)
        enables = self._read_byte(PCF85263_ALARM_ENABLES)
        enables &= 0xE0 # Clear all A1 bits (0-4)
        
        if seconds is not None:
            if not (0 <= seconds <= 59): raise ValueError("Seconds out of range [0-59]")
            buffer[0] = self._dec2bcd(seconds)
            enables |= 0x01
        if minutes is not None:
            if not (0 <= minutes <= 59): raise ValueError("Minutes out of range [0-59]")
            buffer[1] = self._dec2bcd(minutes)
            enables |= 0x02
        if hours is not None:
            if not (0 <= hours <= 23): raise ValueError("Hours out of range [0-23]")
            buffer[2] = self._dec2bcd(hours)
            enables |= 0x04
        if days is not None:
            if not (1 <= days <= 31): raise ValueError("Days out of range [1-31]")
            buffer[3] = self._dec2bcd(days)
            enables |= 0x08
        if months is not None:
            if not (1 <= months <= 12): raise ValueError("Months out of range [1-12]")
            buffer[4] = self._dec2bcd(months)
            enables |= 0x10
            
        self._write_registers(PCF85263_ALARM1_SECONDS, buffer)
        self._write_byte(PCF85263_ALARM_ENABLES, enables)
        
    @property
    def alarm1(self):
        """Returns the current Alarm 1 settings as a tuple: (seconds, minutes, hours, days, months).
        Fields that are disabled (wildcards) return None."""
        enables = self._read_byte(PCF85263_ALARM_ENABLES)
        data = self._read_registers(PCF85263_ALARM1_SECONDS, 5)
        
        seconds = self._bcd2dec(data[0] & 0x7F) if (enables & 0x01) else None
        minutes = self._bcd2dec(data[1] & 0x7F) if (enables & 0x02) else None
        hours = self._bcd2dec(data[2] & 0x3F) if (enables & 0x04) else None
        days = self._bcd2dec(data[3] & 0x3F) if (enables & 0x08) else None
        months = self._bcd2dec(data[4] & 0x1F) if (enables & 0x10) else None
        
        return (seconds, minutes, hours, days, months)
        
    def disable_alarm1(self):
        """Disables Alarm 1 and clears its flag."""
        enables = self._read_byte(PCF85263_ALARM_ENABLES)
        self._write_byte(PCF85263_ALARM_ENABLES, enables & 0xE0)
        self._clear_alarm1_flag()
        
    @property
    def alarm1_triggered(self):
        """Returns True if Alarm 1 has triggered, and clears the flag if it has."""
        flags = self._read_byte(PCF85263_FLAGS)
        triggered = bool(flags & 0x20)
        if triggered:
            self._clear_alarm1_flag()
        return triggered
        
    def _clear_alarm1_flag(self):
        """Clears Alarm 1 triggered flag."""
        # Writing 0 clears the flag, writing 1 has no effect. 
        # Writing ~0x20 avoids unintentionally clearing other flags.
        self._write_byte(PCF85263_FLAGS, 0xFF & ~0x20)

    def set_alarm2(self, minutes=None, hours=None, weekdays=None):
        """Sets Alarm 2. Passing None acts as a wildcard (ignores that field)."""
        buffer = bytearray(3)
        enables = self._read_byte(PCF85263_ALARM_ENABLES)
        enables &= 0x1F # Clear all A2 bits (5-7)
        
        if minutes is not None:
            if not (0 <= minutes <= 59): raise ValueError("Minutes out of range [0-59]")
            buffer[0] = self._dec2bcd(minutes)
            enables |= 0x20
        if hours is not None:
            if not (0 <= hours <= 23): raise ValueError("Hours out of range [0-23]")
            buffer[1] = self._dec2bcd(hours)
            enables |= 0x40
        if weekdays is not None:
            if not (0 <= weekdays <= 6): raise ValueError("Weekdays out of range [0-6]")
            buffer[2] = weekdays # weekday matches naturally
            enables |= 0x80
            
        self._write_registers(PCF85263_ALARM2_MINUTES, buffer)
        self._write_byte(PCF85263_ALARM_ENABLES, enables)
        
    @property
    def alarm2(self):
        """Returns the current Alarm 2 settings as a tuple: (minutes, hours, weekdays).
        Fields that are disabled (wildcards) return None."""
        enables = self._read_byte(PCF85263_ALARM_ENABLES)
        data = self._read_registers(PCF85263_ALARM2_MINUTES, 3)
        
        minutes = self._bcd2dec(data[0] & 0x7F) if (enables & 0x20) else None
        hours = self._bcd2dec(data[1] & 0x3F) if (enables & 0x40) else None
        weekdays = (data[2] & 0x07) if (enables & 0x80) else None
        
        return (minutes, hours, weekdays)
        
    def disable_alarm2(self):
        """Disables Alarm 2 and clears its flag."""
        enables = self._read_byte(PCF85263_ALARM_ENABLES)
        self._write_byte(PCF85263_ALARM_ENABLES, enables & 0x1F)
        self._clear_alarm2_flag()
        
    @property
    def alarm2_triggered(self):
        """Returns True if Alarm 2 has triggered, and clears the flag if it has."""
        flags = self._read_byte(PCF85263_FLAGS)
        triggered = bool(flags & 0x40)
        if triggered:
            self._clear_alarm2_flag()
        return triggered
        
    def _clear_alarm2_flag(self):
        """Clears Alarm 2 triggered flag."""
        # Writing ~0x40 clears only Alarm 2 flag.
        self._write_byte(PCF85263_FLAGS, 0xFF & ~0x40)

