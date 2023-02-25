<div align="center">
 <a href="https://www.python.org">
    <img src="https://forthebadge.com/images/badges/made-with-python.svg">
  </a>
  
# PastUSB
PastUSB is a forensic tool that provides a complete record of USB device activity on both Windows and Linux operating systems. Monitor all USB device insertions and removals, examine information such as device name, manufacturer, and serial number, and uncover any unauthorized access attempts to your computer with PastUSB.
</div>

## Features
- Track the insertion and removal of USB devices on Windows and Linux systems
- View information such as device name, manufacturer, and serial number
- Identify patterns of USB usage
- Detect unauthorized access to computer systems through USB devices

## Requirements
- Windows 7 or later, or Linux operating system
- Python 3.x installed

## Usage

- Clone the repository to your local machine using the following command:

```
git clone https://github.com/Hrishikesh7665/PastUSB.git
```

- Run the script using the following command:

```
python PastUSB.py
```

- or

```
python3 PastUSB.py
```

- The script will output information about all connected USB devices. If you are running the script on Linux, you may need to run it with sudo permissions.

- You can also import the WindowsViewer and LinuxViewer classes from usb_viewer.py into your own Python projects and use them to get information about connected USB devices on Windows and Linux systems, respectively.

- You can use the entire code as a module like this

```
# in test.py

from PastUSB import PastUSB, __version__

allUSBdevices = PastUSB()

for device in allUSBdevices:
    print (device.get_details())
```

## Workflow and Code structure

When the user runs or call the script, the script will check the user's operating system. If the operating system is Windows, it checks if the user has administrator privileges. If the operating system is Linux, it checks if the user is running the script with sudo privileges. If the user does not have the necessary privileges, the script will exit.

The script then calls the get_usb_viewer() function to get an instance of the appropriate viewer. If the operating system is Windows, it creates an instance of the WindowsViewer class. If the operating system is Linux, it creates an instance of the LinuxViewer class.

The viewer's get_usb_devices() method is then called to get a list of USB devices. The method returns a list of USBDevice objects, each containing information about a USB device. The USBDevice object's get_details() method is then called to get a string representation of the USB device's properties. The script prints the string representation of each USB device to the console.

- The code has two entry point, first is if `__name__ == '__main__':` for standalone usage of the code. and second is else part of the `__name__ == '__main__'` which is for using the script as a module and call the module from another script

- Every entry point checks the user's operating system, checks if the user has sufficient permissions, and then calls the appropriate viewer to get USB devices' information.

- <b>BaseViewer</b> classis an abstract class that defines the common properties and methods that all viewer classes must implement.

    - <b> get_usb_devices(self) -> List[USBDevice]</b> This method is responsible for getting a list of connected USB devices. It must be implemented in all viewer classes.

- <b>WindowsViewer</b> class inherits from the <b>BaseViewer</b> class and provides Windows-specific implementation to get USB device information.

    - <b> init(self) </b> This method initializes the class instance.

    - <b> get_usb_devices(self) -> List[USBDevice] </b> This method gets a list of connected USB devices on a Windows system.

    - <b> __get_device_info(self, dev_inst) </b> This method gets the device information for a specified device instance.

- <b>LinuxViewer</b> class that inherits from the <b>BaseViewer</b> class and provides Linux-specific implementation to get USB device information.

    - <b> init(self) </b> This method initializes the class instance.

    - <b> get_usb_devices(self) -> List[USBDevice] </b> This method gets a list of connected USB devices on a Linux system.

    - <b> __get_base_device_info(self) -> List[USBDeviceLinux] </b> This method gets the base information for all connected USB devices on a Linux system.

- <b>USBDevice</b> class represents a USB device and holds its properties.

    - <b> init(self, serial_number: str, first_connect_date: Optional[datetime], last_connect_date: Optional[datetime]) </b> This method initializes the class instance.

    - <b> get_details(self) -> str </b> This method returns a formatted string with the details of the USB device. The string includes the serial number, vendor ID, product ID, version, device size, friendly name, manufacturer, product, and the first and last connection dates.

- <b>USBDeviceWindows</b> <b>USBDeviceLinux</b> both the classes is extend <b>USBDevice</b> class and provides some extra information about the usb devices according the system platform (Windows, Linux)

- <b>open_linux_log_file</b> function is used to handle the linux log file

- <b>parse_windows_log_file</b> <b>parse_linux_log_file</b> two functions are used to parse the log file of the booths the platforms, the <b>parse_linux_log_file</b> use <b>open_linux_log_file</b> function to open the log file

- <b>get_device_info_from_web</b> is a function that take the two argument `vendor_id` and `product_id` and try to get the device information from this https://devicehunt.com website

<b> `N.B: Format Link https://devicehunt.com/view/type/usb/vendor/{vendor_id}/device/{product_id}` </b>

## Output of the Code

{serial_number}: the serial number of the USB device.

{vendor_id}: the vendor ID of the USB device.

{product_id}: the product ID of the USB device.

{version}: the version of the USB device.

{device_size}: the size of the USB device.

{friendly_name}: the friendly name of the USB device.

{manufacturer}: the manufacturer of the USB device.

{product}: the product name of the USB device.

{first_connect_date}: the date and time the USB device was first connected to the computer.

{last_connect_date}: the date and time the USB device was last connected to the computer.


<b> N.B: And some other information depending on the Platform </b>

## Screenshot's
<img alt="PastUSB Proof of Concept" src="../resources/PastUSB_POC.png" height=400 width=500>

## Contributing

If you would like to contribute to PastUSB, please see the [contributing guidelines](./CONTRIBUTING.md) for more information.

## License

This project is licensed under the [MIT License](./LICENSE).
