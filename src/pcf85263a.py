"""
MicroPython library for NXP PCF85263A Real-time clock/calendar.

Initial author: Sebastian Romero (s.romero@arduino.cc)
Copyright (C) Arduino s.r.l. and/or its affiliated companies
"""

from machine import I2C
from micropython import const

_PCF85263A_DEFAULT_ADDRESS = const(0x51)

_PCF85263A_SECONDS_100TH = const(0x00)
_PCF85263A_SECONDS = const(0x01)

_PCF85263A_ALARM1_SECONDS = const(0x08)
_PCF85263A_ALARM2_MINUTES = const(0x0D)
_PCF85263A_ALARM_ENABLES = const(0x10)

_PCF85263A_PIN_IO = const(0x27)
_PCF85263A_FUNCTION = const(0x28)
_PCF85263A_INTA_ENABLE = const(0x29)
_PCF85263A_INTB_ENABLE = const(0x2A)
_PCF85263A_FLAGS = const(0x2B)
_PCF85263A_STOP_ENABLE = const(0x2E)
_PCF85263A_RESETS = const(0x2F)

# Reset commands
_PCF85263A_CMD_CPR = const(0xA4)

# Function register bits
_PCF85263A_FUNC_100TH = const(0x80)
_PCF85263A_FUNC_RTCM = const(0x10)

# Pin IO register bits
_PCF85263A_PINIO_INTAPM_MASK = const(0x03)
_PCF85263A_PINIO_INTAPM_INTA = const(0x02)
_PCF85263A_PINIO_TSPM_MASK = const(0x0C)
_PCF85263A_PINIO_TSPM_INTB = const(0x04)

# Alarm Enablers
_PCF85263A_A1E_SECS = const(0x01)
_PCF85263A_A1E_MINS = const(0x02)
_PCF85263A_A1E_HOURS = const(0x04)
_PCF85263A_A1E_DAYS = const(0x08)
_PCF85263A_A1E_MONS = const(0x10)
_PCF85263A_A1E_MASK = const(0x1F)

_PCF85263A_A2E_MINS = const(0x20)
_PCF85263A_A2E_HOURS = const(0x40)
_PCF85263A_A2E_WDAYS = const(0x80)
_PCF85263A_A2E_MASK = const(0xE0)

# Interrupt bits
_PCF85263A_INT_A1 = const(0x10)
_PCF85263A_INT_A2 = const(0x08)

# Flag bits (Register 0x2B)
_PCF85263A_FLAG_A1 = const(0x20)
_PCF85263A_FLAG_A2 = const(0x40)

class PCF85263A:
    """PCF85263A RTC driver class."""

    def __init__(self, i2c=None, address=_PCF85263A_DEFAULT_ADDRESS):
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
        """Writes a single byte to the specified register."""
        self._bytebuf[0] = val
        self.i2c.writeto_mem(self.address, reg, self._bytebuf)

    def _read_byte(self, reg):
        """Reads a single byte from the specified register."""
        self.i2c.readfrom_mem_into(self.address, reg, self._bytebuf)
        return self._bytebuf[0]
        
    def _read_registers(self, reg, count):
        """Reads multiple bytes starting from the specified register."""
        assert count <= len(self._buffer), "Read count exceeds buffer size"
        view = memoryview(self._buffer)[0:count]
        self.i2c.readfrom_mem_into(self.address, reg, view)
        return view
        
    def _write_registers(self, reg, buffer):
        """Writes multiple bytes starting from the specified register."""
        self.i2c.writeto_mem(self.address, reg, buffer)
        
    def _bcd2dec(self, bcd):
        """Converts Binary Coded Decimal (BCD) to decimal."""
        return (((bcd & 0xF0) >> 4) * 10 + (bcd & 0x0F))

    def _dec2bcd(self, dec):
        """Converts decimal to Binary Coded Decimal (BCD)."""
        tens, units = divmod(dec, 10)
        return (tens << 4) + units
        
    def _set_rtc_mode(self):
        """Configures the RTC to run in Real-Time Clock mode."""
        # _PCF85263A_FUNCTION register
        # mode 0: RTC mode, mode 1: Stopwatch mode
        mask = self._read_byte(_PCF85263A_FUNCTION)
        mask &= ~_PCF85263A_FUNC_RTCM  # Clear bit 4 (RTCM)
        mask &= ~_PCF85263A_FUNC_100TH # Clear bit 7 (100TH) to save power
        self._write_byte(_PCF85263A_FUNCTION, mask)

    def _set_stopwatch_mode(self):
        """Configures the RTC to run in Stopwatch mode."""
        # _PCF85263A_FUNCTION register
        mask = self._read_byte(_PCF85263A_FUNCTION)
        mask |= _PCF85263A_FUNC_RTCM  # Set bit 4 (RTCM)
        mask |= _PCF85263A_FUNC_100TH  # Set bit 7 (100TH) to enable hundredths
        self._write_byte(_PCF85263A_FUNCTION, mask)
        
    def stop(self):
        """Stops the entire RTC clock. Note: This is not just for the stopwatch."""
        self._write_byte(_PCF85263A_STOP_ENABLE, 1)
        
    def start(self):
        """Starts the entire RTC clock. Note: This is not just for the stopwatch."""
        self._write_byte(_PCF85263A_STOP_ENABLE, 0)
        
    @property
    def stopped(self):
        """Returns True if the RTC clock is stopped, False otherwise."""
        return self._read_byte(_PCF85263A_STOP_ENABLE) == 1
        
    def software_reset(self):
        """Performs a software reset of the RTC (Clears also prescaler and timestamp)."""
        self._write_byte(_PCF85263A_RESETS, 0x2C)

    @property
    def oscillator_stopped(self):
        """Returns True if the oscillator is stopped. If True, it might indicate an undervoltage issue."""
        return bool(self._read_byte(_PCF85263A_SECONDS) & 0x80)

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
        data = self._read_registers(_PCF85263A_SECONDS, 7)
        
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
        """Sets the current datetime of the RTC."""
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
        self._write_registers(_PCF85263A_SECONDS, buffer)
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
        data = self._read_registers(_PCF85263A_SECONDS_100TH, 6)
        
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
        """
        Sets the current stopwatch time.
        Stops the stopwatch when setting the time.
        """
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
        self._write_registers(_PCF85263A_SECONDS_100TH, buffer)

    def stopwatch_reset(self):
        """Resets the stopwatch to 0 and stops it."""
        self.stopwatch_time = (0, 0, 0, 0)

    @property
    def stopwatch_mode(self):
        """Get or set the RTC mode to Real-Time Clock (False) or Stopwatch (True)."""
        mask = self._read_byte(_PCF85263A_FUNCTION)
        return bool(mask & _PCF85263A_FUNC_RTCM)

    @stopwatch_mode.setter
    def stopwatch_mode(self, is_stopwatch):
        """
        Sets the RTC mode to Real-Time Clock (False) or Stopwatch (True).
        When enabling stopwatch mode, the RTC is automatically stopped.
        When disabling stopwatch mode, the RTC is automatically started.
        """
        if is_stopwatch:
            self.stop()
            self._set_stopwatch_mode()
        else:
            self.stop()
            self._write_byte(_PCF85263A_RESETS, _PCF85263A_CMD_CPR) # Clear prescaler (CPR command), triggers swap from stopwatch time to RTC time
            self._set_rtc_mode()
            self.start()

    def _configure_interrupt_pin(self, pin, enable):
        """Internal helper to configure PIN_IO bits for INTA or INTB."""
        pin_io = self._read_byte(_PCF85263A_PIN_IO)
        if pin == 'inta':
            # INTAPM is bits 1:0
            pin_io &= ~_PCF85263A_PINIO_INTAPM_MASK # Clear bits 1:0
            if enable:
                pin_io |= _PCF85263A_PINIO_INTAPM_INTA # Set to 10 (INTA output)
        elif pin == 'intb':
            # TSPM is bits 3:2
            pin_io &= ~_PCF85263A_PINIO_TSPM_MASK # Clear bits 3:2
            if enable:
                pin_io |= _PCF85263A_PINIO_TSPM_INTB # Set to 01 (INTB output)
        self._write_byte(_PCF85263A_PIN_IO, pin_io)

    def set_alarm1(self, second=None, minute=None, hour=None, day=None, month=None):
        """Sets Alarm 1. Passing None acts as a wildcard (ignores that field)."""
        buffer = bytearray(5)
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        enables &= ~_PCF85263A_A1E_MASK # Clear all A1 bits (0-4)
        
        if second is not None:
            if not (0 <= second <= 59): raise ValueError("Second out of range [0-59]")
            buffer[0] = self._dec2bcd(second)
            enables |= _PCF85263A_A1E_SECS
        if minute is not None:
            if not (0 <= minute <= 59): raise ValueError("Minute out of range [0-59]")
            buffer[1] = self._dec2bcd(minute)
            enables |= _PCF85263A_A1E_MINS
        if hour is not None:
            if not (0 <= hour <= 23): raise ValueError("Hour out of range [0-23]")
            buffer[2] = self._dec2bcd(hour)
            enables |= _PCF85263A_A1E_HOURS
        if day is not None:
            if not (1 <= day <= 31): raise ValueError("Day out of range [1-31]")
            buffer[3] = self._dec2bcd(day)
            enables |= _PCF85263A_A1E_DAYS
        if month is not None:
            if not (1 <= month <= 12): raise ValueError("Month out of range [1-12]")
            buffer[4] = self._dec2bcd(month)
            enables |= _PCF85263A_A1E_MONS
            
        self._write_registers(_PCF85263A_ALARM1_SECONDS, buffer)
        self._write_byte(_PCF85263A_ALARM_ENABLES, enables)
        
    @property
    def alarm1(self):
        """Returns the current Alarm 1 settings as a tuple: (second, minute, hour, day, month).
        Fields that are disabled (wildcards) return None."""
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        data = self._read_registers(_PCF85263A_ALARM1_SECONDS, 5)
        
        second = self._bcd2dec(data[0] & 0x7F) if (enables & _PCF85263A_A1E_SECS) else None
        minute = self._bcd2dec(data[1] & 0x7F) if (enables & _PCF85263A_A1E_MINS) else None
        hour = self._bcd2dec(data[2] & 0x3F) if (enables & _PCF85263A_A1E_HOURS) else None
        day = self._bcd2dec(data[3] & 0x3F) if (enables & _PCF85263A_A1E_DAYS) else None
        month = self._bcd2dec(data[4] & 0x1F) if (enables & _PCF85263A_A1E_MONS) else None
        
        return (second, minute, hour, day, month)

    @property
    def alarm1_inta_enabled(self):
        """Returns True if Alarm 1 INTA routing is enabled."""
        return bool(self._read_byte(_PCF85263A_INTA_ENABLE) & _PCF85263A_INT_A1)

    @alarm1_inta_enabled.setter
    def alarm1_inta_enabled(self, enable):
        """Enables or disables Alarm 1 INTA routing."""
        inta_en = self._read_byte(_PCF85263A_INTA_ENABLE)
        if enable:
            inta_en |= _PCF85263A_INT_A1
            self._configure_interrupt_pin('inta', True)
        else:
            inta_en &= ~_PCF85263A_INT_A1
        self._write_byte(_PCF85263A_INTA_ENABLE, inta_en)

    @property
    def alarm1_intb_enabled(self):
        """Returns True if Alarm 1 INTB routing is enabled."""
        return bool(self._read_byte(_PCF85263A_INTB_ENABLE) & _PCF85263A_INT_A1)

    @alarm1_intb_enabled.setter
    def alarm1_intb_enabled(self, enable):
        """Enables or disables Alarm 1 INTB routing."""
        intb_en = self._read_byte(_PCF85263A_INTB_ENABLE)
        if enable:
            intb_en |= _PCF85263A_INT_A1
            self._configure_interrupt_pin('intb', True)
        else:
            intb_en &= ~_PCF85263A_INT_A1
        self._write_byte(_PCF85263A_INTB_ENABLE, intb_en)
        
    def disable_alarm1(self):
        """Disables Alarm 1 and clears its flag."""
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        self._write_byte(_PCF85263A_ALARM_ENABLES, enables & ~_PCF85263A_A1E_MASK)
        
        # Clear interrupt routing (Bit 4)
        inta_en = self._read_byte(_PCF85263A_INTA_ENABLE)
        self._write_byte(_PCF85263A_INTA_ENABLE, inta_en & ~_PCF85263A_INT_A1)
        intb_en = self._read_byte(_PCF85263A_INTB_ENABLE)
        self._write_byte(_PCF85263A_INTB_ENABLE, intb_en & ~_PCF85263A_INT_A1)
        
        self.clear_alarm1_flag()
        
    @property
    def alarm1_triggered(self):
        """Returns True if Alarm 1 has triggered, and clears the flag if it has."""
        flags = self._read_byte(_PCF85263A_FLAGS)
        triggered = bool(flags & _PCF85263A_FLAG_A1)
        if triggered:
            self.clear_alarm1_flag()
        return triggered
        
    def clear_alarm1_flag(self):
        """Clears Alarm 1 triggered flag."""
        # Writing 0 clears the flag, writing 1 has no effect. 
        # Writing ~_PCF85263A_FLAG_A1 avoids unintentionally clearing other flags.
        self._write_byte(_PCF85263A_FLAGS, 0xFF & ~_PCF85263A_FLAG_A1)

    def set_stopwatch_alarm1(self, hour=None, minute=None, second=None):
        """
        Sets Alarm 1 in stopwatch mode. Passing None acts as a wildcard (ignores that field).
        
        Parameters:
            hour: 0-999999
            minute: 0-59
            second: 0-59
        """
        buffer = bytearray(5)
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        enables &= ~_PCF85263A_A1E_MASK # Clear all A1 bits (0-4)
        
        if second is not None:
            if not (0 <= second <= 59): raise ValueError("Second out of range [0-59]")
            buffer[0] = self._dec2bcd(second)
            enables |= _PCF85263A_A1E_SECS
            
        if minute is not None:
            if not (0 <= minute <= 59): raise ValueError("Minute out of range [0-59]")
            buffer[1] = self._dec2bcd(minute)
            enables |= _PCF85263A_A1E_MINS
            
        if hour is not None:
            if not (0 <= hour <= 999999): raise ValueError("Hour out of range [0-999999]")
            buffer[2] = self._dec2bcd(hour % 100)
            buffer[3] = self._dec2bcd((hour % 10000) // 100)
            buffer[4] = self._dec2bcd(hour // 10000)
            enables |= (_PCF85263A_A1E_HOURS | _PCF85263A_A1E_DAYS | _PCF85263A_A1E_MONS)
            
        self._write_registers(_PCF85263A_ALARM1_SECONDS, buffer)
        self._write_byte(_PCF85263A_ALARM_ENABLES, enables)
        
    @property
    def stopwatch_alarm1(self):
        """Returns the current Alarm 1 settings for stopwatch mode as a tuple: (hour, minute, second).
        Fields that are disabled (wildcards) return None."""
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        data = self._read_registers(_PCF85263A_ALARM1_SECONDS, 5)
        
        second = self._bcd2dec(data[0] & 0x7F) if (enables & _PCF85263A_A1E_SECS) else None
        minute = self._bcd2dec(data[1] & 0x7F) if (enables & _PCF85263A_A1E_MINS) else None
        
        # In stopwatch mode, hours uses 3 registers
        if (enables & _PCF85263A_A1E_HOURS) and (enables & _PCF85263A_A1E_DAYS) and (enables & _PCF85263A_A1E_MONS):
            hours_L = self._bcd2dec(data[2] & 0xFF)
            hours_M = self._bcd2dec(data[3] & 0xFF)
            hours_H = self._bcd2dec(data[4] & 0xFF)
            hour = hours_H * 10000 + hours_M * 100 + hours_L
        else:
            hour = None
            
        return (hour, minute, second)

    def set_alarm2(self, minute=None, hour=None, weekday=None):
        """Sets Alarm 2. Passing None acts as a wildcard (ignores that field)."""
        buffer = bytearray(3)
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        enables &= ~_PCF85263A_A2E_MASK # Clear all A2 bits (5-7)
        
        if minute is not None:
            if not (0 <= minute <= 59): raise ValueError("Minute out of range [0-59]")
            buffer[0] = self._dec2bcd(minute)
            enables |= _PCF85263A_A2E_MINS
        if hour is not None:
            if not (0 <= hour <= 23): raise ValueError("Hour out of range [0-23]")
            buffer[1] = self._dec2bcd(hour)
            enables |= _PCF85263A_A2E_HOURS
        if weekday is not None:
            if not (0 <= weekday <= 6): raise ValueError("Weekday out of range [0-6]")
            buffer[2] = weekday # weekday matches naturally
            enables |= _PCF85263A_A2E_WDAYS
            
        self._write_registers(_PCF85263A_ALARM2_MINUTES, buffer)
        self._write_byte(_PCF85263A_ALARM_ENABLES, enables)
        
    @property
    def alarm2(self):
        """Returns the current Alarm 2 settings as a tuple: (minute, hour, weekday).
        Fields that are disabled (wildcards) return None."""
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        data = self._read_registers(_PCF85263A_ALARM2_MINUTES, 3)
        
        minute = self._bcd2dec(data[0] & 0x7F) if (enables & _PCF85263A_A2E_MINS) else None
        hour = self._bcd2dec(data[1] & 0x3F) if (enables & _PCF85263A_A2E_HOURS) else None
        weekday = (data[2] & 0x07) if (enables & _PCF85263A_A2E_WDAYS) else None
        
        return (minute, hour, weekday)

    @property
    def alarm2_inta_enabled(self):
        """Returns True if Alarm 2 INTA routing is enabled."""
        return bool(self._read_byte(_PCF85263A_INTA_ENABLE) & _PCF85263A_INT_A2)

    @alarm2_inta_enabled.setter
    def alarm2_inta_enabled(self, enable):
        """Enables or disables Alarm 2 INTA routing."""
        inta_en = self._read_byte(_PCF85263A_INTA_ENABLE)
        if enable:
            inta_en |= _PCF85263A_INT_A2
            self._configure_interrupt_pin('inta', True)
        else:
            inta_en &= ~_PCF85263A_INT_A2
        self._write_byte(_PCF85263A_INTA_ENABLE, inta_en)

    @property
    def alarm2_intb_enabled(self):
        """Returns True if Alarm 2 INTB routing is enabled."""
        return bool(self._read_byte(_PCF85263A_INTB_ENABLE) & _PCF85263A_INT_A2)

    @alarm2_intb_enabled.setter
    def alarm2_intb_enabled(self, enable):
        """Enables or disables Alarm 2 INTB routing."""
        intb_en = self._read_byte(_PCF85263A_INTB_ENABLE)
        if enable:
            intb_en |= _PCF85263A_INT_A2
            self._configure_interrupt_pin('intb', True)
        else:
            intb_en &= ~_PCF85263A_INT_A2
        self._write_byte(_PCF85263A_INTB_ENABLE, intb_en)
        
    def disable_alarm2(self):
        """Disables Alarm 2 and clears its flag."""
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        self._write_byte(_PCF85263A_ALARM_ENABLES, enables & ~_PCF85263A_A2E_MASK)
        
        # Clear interrupt routing (Bit 3)
        inta_en = self._read_byte(_PCF85263A_INTA_ENABLE)
        self._write_byte(_PCF85263A_INTA_ENABLE, inta_en & ~_PCF85263A_INT_A2)
        intb_en = self._read_byte(_PCF85263A_INTB_ENABLE)
        self._write_byte(_PCF85263A_INTB_ENABLE, intb_en & ~_PCF85263A_INT_A2)
        
        self.clear_alarm2_flag()
        
    @property
    def alarm2_triggered(self):
        """Returns True if Alarm 2 has triggered, and clears the flag if it has."""
        flags = self._read_byte(_PCF85263A_FLAGS)
        triggered = bool(flags & _PCF85263A_FLAG_A2)
        if triggered:
            self.clear_alarm2_flag()
        return triggered
        
    def clear_alarm2_flag(self):
        """Clears Alarm 2 triggered flag."""
        # Writing ~_PCF85263A_FLAG_A2 clears only Alarm 2 flag.
        self._write_byte(_PCF85263A_FLAGS, 0xFF & ~_PCF85263A_FLAG_A2)

    def set_stopwatch_alarm2(self, hour=None, minute=None):
        """
        Sets Alarm 2 in stopwatch mode. Passing None acts as a wildcard (ignores that field).
        
        Parameters:
            hour: 0-9999
            minute: 0-59
        """
        buffer = bytearray(3)
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        enables &= ~_PCF85263A_A2E_MASK # Clear all A2 bits (5-7)
        
        if minute is not None:
            if not (0 <= minute <= 59): raise ValueError("Minute out of range [0-59]")
            buffer[0] = self._dec2bcd(minute)
            enables |= _PCF85263A_A2E_MINS
            
        if hour is not None:
            if not (0 <= hour <= 9999): raise ValueError("Hour out of range [0-9999]")
            buffer[1] = self._dec2bcd(hour % 100)
            buffer[2] = self._dec2bcd(hour // 100)
            enables |= (_PCF85263A_A2E_HOURS | _PCF85263A_A2E_WDAYS)
            
        self._write_registers(_PCF85263A_ALARM2_MINUTES, buffer)
        self._write_byte(_PCF85263A_ALARM_ENABLES, enables)
        
    @property
    def stopwatch_alarm2(self):
        """Returns the current Alarm 2 settings for stopwatch mode as a tuple: (hour, minute).
        Fields that are disabled (wildcards) return None."""
        enables = self._read_byte(_PCF85263A_ALARM_ENABLES)
        data = self._read_registers(_PCF85263A_ALARM2_MINUTES, 3)
        
        minute = self._bcd2dec(data[0] & 0x7F) if (enables & _PCF85263A_A2E_MINS) else None
        
        # In stopwatch mode, hours uses 2 registers
        if (enables & _PCF85263A_A2E_HOURS) and (enables & _PCF85263A_A2E_WDAYS):
            hours_L = self._bcd2dec(data[1] & 0xFF)
            hours_M = self._bcd2dec(data[2] & 0xFF)
            hour = hours_M * 100 + hours_L
        else:
            hour = None
            
        return (hour, minute)
