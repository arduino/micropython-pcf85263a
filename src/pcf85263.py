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

PCF85263_FUNCTION = const(0x28)
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
        mask &= 0xEF  # Clear bit 4
        self._write_byte(PCF85263_FUNCTION, mask)
        
    def stop(self):
        """Stops the entire RTC clock. Note: This is not just for the stopwatch."""
        self._write_byte(PCF85263_STOP_ENABLE, 1)
        
    def start(self):
        """Starts the entire RTC clock. Note: This is not just for the stopwatch."""
        self._write_byte(PCF85263_STOP_ENABLE, 0)
        
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
