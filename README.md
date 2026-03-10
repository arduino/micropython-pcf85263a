# 📦 PCF85263A MicroPython Driver

This package contains a MicroPython API to connect to the NXP PCF85263A Real-Time Clock (RTC). 

## ✨ Features

- **Datetime Operations**: Easy-to-use datetime property for reading and setting: `(year, month, mday, hour, minute, second, weekday, yearday)`.
- **Stopwatch Mode**: Configurable mode to track elapsed time (up to 999,999 hours) with hundredths-of-a-second precision, plus reset capabilities.
- **Alarms & Interrupts**: Comprehensive support for Alarm 1 and Alarm 2 (in both RTC and Stopwatch modes), with polling or dedicated hardware interrupt routing (`INTA`, `INTB`).
- **Clock Control & Diagnostics**: Provides simple `start()`, `stop()`, and `software_reset()` methods, plus undervoltage/stop detection via `oscillator_stopped`.
- **Easy I2C integration**: Standard MicroPython `machine.I2C` compatibility allowing it to be used on any microcontroller supporting I2C via MicroPython.

## 📖 Documentation
To generate API documentation, `pydoc-markdown` can be run which parses the driver docstrings into markdown format inside the `docs/` folder.

## ✅ Supported Boards

Any board that has I2C and can run a modern version of MicroPython is supported. You will have to specify the I2C interface to be used. e.g. `rtc = PCF85263A(I2C(0))`. 

## ⚙️ Installation

The easiest way is to use the [Arduino MicroPython Package Installer](https://github.com/arduino/lab-micropython-package-installer/releases/latest). Otherwise you can use [mpremote and mip](https://docs.micropython.org/en/latest/reference/packages.html#packages): 

```bash
mpremote mip install github:arduino/micropython-pcf85263a
```

## 🧑‍💻 Developer Installation

The easiest way is to clone the repository and then run the example using `mpremote`.
The recommended way is to mount the root directory remotely on the board and then running an example script. e.g.

```
mpremote connect <port> mount src run ./examples/basic_usage.py
```

If your board cannot be detected automatically you can try to explicitly specify the board's serial or port. For example:

```
mpremote connect /dev/ttyACM0 mount src run ./examples/basic_usage.py
```

## 🐛 Reporting Issues

If you encounter any issue, please open a bug report [here](https://github.com/arduino/pcf85263aat-micropython/issues). 

## 💪 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 🤙 Contact

For questions, comments, or feedback on this package, please create an issue on this repository.
