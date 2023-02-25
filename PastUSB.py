# Import all required modules
from typing import List, Tuple, Dict, Any, Optional, Iterator, IO
import abc, glob, os, gzip, ctypes, platform
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import urllib.request
import urllib.error

# 'winreg' is not available for linux so it will be used only on windows
if platform.system() == 'Windows' :
    import winreg

__version__ = "1.0.0"
# Colors
light_red = "\u001b[38;5;208m"
red = "\u001b[38;5;160m"
green = "\033[0;32m"
yellow = "\u001b[38;5;184m"
nocolor = "\033[0m"
ascii_col = "\033[36m"
log_col = "\u001b[38;5;110m"

'''
convert_binary_to_ascii_string() function takes a binary string as input and returns a corresponding ASCII string 
by converting each byte of the binary string into its corresponding ASCII character. It filters out any byte
that has a value of 0 or is greater than or equal to 128, as those values are not valid ASCII characters.
The function uses a list comprehension to iterate over the bytes of the input binary string and apply the
chr() function to each byte to get its ASCII character representation.
The resulting characters are then joined together into a single string using the ''.join() method.
'''
def convert_binary_to_ascii_string(binary_string: bytes) -> str:
    return ''.join([chr(byte) for byte in binary_string if 0 < byte < 128])


'''
convert_windows_time_to_unix() function takes a Windows timestamp as input and returns the corresponding
Unix timestamp. It first defines two constants: "windows_tick" and "seconds_to_unix_epoch".
"windows_tick" represents the number of 100-nanosecond intervals that have elapsed since January 1, 1601, 
while "seconds_to_unix_epoch" represents the number of seconds between January 1, 1601, and January 1, 1970,
which is the Unix epoch. The function then calculates the number of seconds that have elapsed between
the Windows epoch and the Unix epoch by dividing the input "windows_timestamp" by "windows_tick" to get
the number of ticks that have elapsed, subtracting "seconds_to_unix_epoch" from that value to account for
the difference in epoch times, and converting the result to an integer using the int() function.
The resulting value represents the corresponding Unix timestamp.
NB: This function is only needed for windows systems
'''
def convert_windows_time_to_unix(windows_timestamp: int) -> int:
    windows_tick = 10000000
    seconds_to_unix_epoch = 11644473600
    return int(windows_timestamp / windows_tick - seconds_to_unix_epoch)


'''
parse_windows_log_file() function takes the file path of a Windows log file as input and returns an iterator
that yields a list of strings for each log section found in the file. A log section is defined as a series
of lines starting with '>>>' and ending with '<<<'. The function opens the file using the 'iso-8859-1' encoding,
reads the file line by line, and checks each line to see if it is the start or end of a log section.
If the line is the start of a log section, the function reads the next line to check if it is also the start
of a log section, and if so, it adds both lines to the current log section. If the line is the end of a log
section, the function reads the next line to check if it is also the end of a log section, and if so,
it adds both lines to the current log section, yields the log section, clears it, and continues reading the file.
If the function encounters a line that is not the start or end of a log section but is inside a log section,
it adds the line to the current log section. The function returns an iterator that yields the log sections found
in the file one at a time.
NB: This function is only for windows systems
'''
def parse_windows_log_file(filepath: str) -> Iterator[List[str]]:
    with open(filepath, 'r', encoding="iso-8859-1") as log_file:
        log_section = []
        for line in log_file:
            if len(log_section) == 0 and line.startswith('>>>'):
                next_line = next(log_file)
                if next_line.startswith('>>>'):
                    log_section.append(line)
                    log_section.append(next_line)
                    continue
            if len(log_section) > 0 and line.startswith('<<<'):
                next_line = next(log_file)
                if next_line.startswith('<<<'):
                    log_section.append(line)
                    log_section.append(next_line)
                    yield log_section
                    log_section.clear()
                    continue
            if len(log_section) > 0:
                log_section.append(line)


'''
get_device_info_from_web() function takes two strings representing a USB device's vendor ID and product ID,
and an optional integer max_attempts that defaults to 3, as input. It attempts to fetch the device information
from devicehunt.com by constructing a URL using the input vendor and product IDs, and then opening that URL
using urllib. If the attempt to fetch the device information fails, the function returns a tuple of None values.
If the attempt succeeds, the function parses the HTML response to extract the vendor name and device description,
if present. It searches for the vendor name and device description by finding the start and end of
the corresponding HTML tags in the response, and then extracting the text between those tags.
If the vendor name or device description cannot be found in the response, the function returns a tuple of
None values. Otherwise, the function returns a tuple of the extracted vendor name and device description.
'''
def get_device_info_from_web(vendor_id: str, product_id: str, max_attempts: int = 3) -> Tuple[Optional[str], Optional[str]]:
    if max_attempts <= 0:
        return None, None
    url = f'https://devicehunt.com/view/type/usb/vendor/{vendor_id}/device/{product_id}'
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
    except urllib.error.URLError as e:
        html = '{ "vendor" : "Error to fetch",  "device" : "Error to fetch"}'
    start_vendor = html.find('--type-vendor')
    if start_vendor == -1:
        vendor_name = None
    else:
        start_vendor = html.find('details__heading', start_vendor) + 17
        end_vendor = html.find('<', start_vendor)
        vendor_name = (html[start_vendor:end_vendor].strip()).replace('>\n', '')
    start_device = html.find('--type-device')
    if start_device == -1:
        device_description = None
    else:
        start_device = html.find('details__heading', start_device) + 17
        end_device = html.find('<', start_device)
        device_description = (html[start_device:end_device].strip()).replace('>\n', '')
    return vendor_name, device_description


'''
open_linux_log_file() function takes a string filepath as input and returns an IO object for reading the file.
If the file path ends with '.gz', the function returns a gzip.open IO object for reading the gzip-compressed
file with 'rt' mode. Otherwise, the function returns a regular open IO object for reading the file with 'r' mode.
The returned IO object can be used to read the contents of the file.
NB: This function is only for Linux systems
'''
def open_linux_log_file(filepath: str) -> IO:
    if filepath.endswith('.gz'):
        return gzip.open(filepath, 'rt')
    else:
        return open(filepath, 'r')


'''
parse_linux_log_file() function takes a string filepath as input and returns an iterator over lists of strings.
The function reads the contents of the specified file using the
open_linux_log_file function() [the previous function], and then iterates over each line of the file.

If a line contains the substring "New USB device found", the function checks whether there is any existing
data in the section list. If the section list is empty, the function appends the line to the section list
and continues to the next line. If the section list is not empty, the function clears the section list and
appends the line to it.

If the section list is not empty, the function appends the current line to the section list. If the line
contains the substring "Mounted /dev/sd", the function yields the section list, clears it, and continues
to the next line.

The yield statement returns the current value of the section list as a new list, and then pauses the
function until the next value is requested by the iterator. This process repeats until the end of the
file is reached, at which point the function terminates.
'''
def parse_linux_log_file(filepath: str) -> Iterator[List[str]]:
    with open_linux_log_file(filepath) as log_file:
        section = []
        for line in log_file:
            if 'New USB device found' in line:
                if len(section) == 0:
                    section.append(line)
                    continue
                else:
                    section.clear()
                    section.append(line)
            if len(section) > 0:
                section.append(line)
                if 'Mounted /dev/sd' in line:
                    yield section
                    section.clear()


'''
Defines a data class called USBDevice, which represents a USB device with various properties such as version,
serial number, friendly name, vendor ID, product ID, and dates of first and last connection.
The class also has a method called get_details, which returns a string representation of the device's
properties in a formatted way.
NB: Dataclass decorator is used for automatically generate methods 
'''
@dataclass(init=True, repr=True, eq=False)
class USBDevice:
    version: Optional[str] = None
    serial_number: Optional[str] = None
    friendly_name: Optional[str] = None
    vendor_id: Optional[str] = None
    product_id: Optional[str] = None
    first_connect_date: Optional[datetime] = None
    last_connect_date: Optional[datetime] = None
    vendor_name: Optional[str] = None
    product_description: Optional[str] = None
    def get_details(self) -> str:
        details = f'Device: {self.friendly_name}\n'
        details += f'Vendor Name: {self.vendor_name}\n'
        details += f'Product Description: {self.product_description}\n'
        details += f'First Connect Date: {self.first_connect_date}\n'
        details += f'Last Connect Date: {self.last_connect_date}\n'
        details += f'Serial Number: {self.serial_number}\n'
        details += f'Vendor ID: {self.vendor_id}\n'
        details += f'Product ID: {self.product_id}\n'
        details += f'Version: {self.version}\n'
        return details


'''
Defines a new class USBDeviceWindows that inherits from the USBDevice class.
It adds four new attributes: usbstor_vendor, usbstor_product, parent_prefix_id, and guid, which are specific
to USB devices on Windows.
Overrides the get_details() method of the base class to include the new attributes in the returned string.
This new class can be used to represent USB devices on Windows and includes additional information about
the device compared to the base USBDevice class.
NB: This class is only invoked when the device is windows
'''
@dataclass(init=True, repr=True, eq=False)
class USBDeviceWindows(USBDevice):
    usbstor_vendor: Optional[str] = None
    usbstor_product: Optional[str] = None
    parent_prefix_id: Optional[str] = None
    guid: Optional[str] = None
    drive_letter: Optional[str] = None
    def get_details(self) -> str:
        details = super().get_details()
        details += f'USBSTOR Vendor: {self.usbstor_vendor}\n'
        details += f'USBSTOR Product: {self.usbstor_product}\n'
        details += f'Drive Name: {self.drive_letter}\n'
        details += f'GUID: {self.guid}\n'
        details += f'Parent Prefix ID: {self.parent_prefix_id}\n'
        return details


'''
Defines a data class USBDeviceLinux that extends the USBDevice class with additional attributes specific to
Linux systems. The additional attributes include syslog_manufacturer, syslog_product, and device_size.
Overrides the get_details() method of the parent class to include the new attributes in the returned
details string.
NB: This class is only invoked when the device is Linux
'''
@dataclass(init=True, repr=True, eq=False)
class USBDeviceLinux(USBDevice):
    syslog_manufacturer: Optional[str] = None
    syslog_product: Optional[str] = None
    device_size: Optional[str] = None
    def get_details(self) -> str:
        details = super().get_details()
        details += f'SYSLOG Manufacturer: {self.syslog_manufacturer}\n'
        details += f'SYSLOG Product: {self.syslog_product}\n'
        details += f'Device size: {self.device_size}\n'
        return details


'''
Defines an abstract base class called BaseViewer using the abc module. This class has an abstract method called
get_usb_devices() that returns a list of USBDevice objects. It also has a static method _set_devices_info
that takes a list of USBDevice objects as input and sets additional information on each device by calling
previously defined get_device_info_from_web() function to get information about the vendor and product based on
their IDs. This method is intended to be used by subclasses of BaseViewer to set additional information on the
USB devices they retrieve.
'''
class BaseViewer(abc.ABC):
    @abc.abstractmethod
    def get_usb_devices(self) -> List[USBDevice]:
        pass
    @staticmethod
    def _set_devices_info(usb_devices: List[USBDevice]) -> None:
        for device in usb_devices:
            if device.vendor_id is not None and device.product_id is not None:
                vendor_name, product_description = get_device_info_from_web(device.vendor_id, device.product_id)
                device.vendor_name = vendor_name
                device.product_description = product_description


'''
The WindowsViewer class, which is inherits from BaseViewer. It provides a method get_usb_devices that returns a
list of USBDevice objects containing information about the USB devices connected to a Windows machine.
The WindowsViewer class has several private class-level variables representing Windows Registry paths, such as
__USBSTOR_PATH, __USB_PATH, __MOUNTED_DEVICES_PATH, __PORTABLE_DEVICES_PATH, and __MOUNT_POINTS_PATH.
The get_usb_devices method calls several private instance methods to gather information about connected USB
devices. These private methods include:
__get_base_device_info: This method retrieves basic device information by parsing the Windows Registry keys
located at the __USBSTOR_PATH location.
__set_vendor_and_product_ids: This method sets the vendor and product IDs for each device by parsing the
Windows Registry keys located at the __USB_PATH location.
__set_guids: This method sets the GUID for each device by parsing the Windows Registry values located
at the __MOUNTED_DEVICES_PATH location.
__set_drive_letters: This method sets the drive letter for each device by parsing the Windows Registry values
located at the __PORTABLE_DEVICES_PATH location.
__set_first_connect_dates: This static method sets the first connect date for each device by parsing the
Windows setupapi.dev.log files located at the C:\Windows\inf\ directory. It uses a helper function
parse_windows_log_file to parse these files.
'''
# Main code for windows systems and here we need the winreg module to retrieve data from the registry
if platform.system() == 'Windows':
    class WindowsViewer(BaseViewer):
        __USBSTOR_PATH = r'SYSTEM\CurrentControlSet\Enum\USBSTOR'
        __USB_PATH = r'SYSTEM\CurrentControlSet\Enum\USB'
        __MOUNTED_DEVICES_PATH = r'SYSTEM\MountedDevices'
        __PORTABLE_DEVICES_PATH = r'SOFTWARE\Microsoft\Windows Portable Devices\Devices'
        __MOUNT_POINTS_PATH = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\MountPoints2'
        def __init__(self):
            self.__machine_registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            self.__user_registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        def __del__(self):
            self.__machine_registry.Close()
            self.__user_registry.Close()
        def get_usb_devices(self) -> List[USBDevice]:
            usb_devices = self.__get_base_device_info()
            self.__set_vendor_and_product_ids(usb_devices)
            self.__set_guids(usb_devices)
            self.__set_drive_letters(usb_devices)
            self.__set_first_connect_dates(usb_devices)
            self.__set_last_connect_dates(usb_devices)
            self._set_devices_info(usb_devices)
            return usb_devices
        def __get_base_device_info(self) -> List[USBDeviceWindows]:
            root_key = winreg.OpenKey(self.__machine_registry, WindowsViewer.__USBSTOR_PATH)
            usbstor_keys = self.__get_registry_keys(root_key)
            usb_devices = []
            for key_str in usbstor_keys:
                device_attributes = self.__parse_device_name(key_str)
                if device_attributes is None:
                    continue
                vendor, product, version = device_attributes
                usb_path = rf'{WindowsViewer.__USBSTOR_PATH}\{key_str}'
                usb_key = winreg.OpenKey(self.__machine_registry, usb_path)
                devices_keys = self.__get_registry_keys(usb_key)
                for device in devices_keys:
                    device_key = winreg.OpenKey(self.__machine_registry, rf'{usb_path}\{device}')
                    device_values = self.__get_registry_values(device_key)
                    serial_number = device.split('&')[0]
                    friendly_name = device_values['FriendlyName']
                    if 'ParentPrefixId' in device_values:
                        parent_prefix_id = device_values['ParentPrefixId']
                    else:
                        parent_prefix_id = device
                    usb_device = USBDeviceWindows(
                        usbstor_vendor=vendor,
                        usbstor_product=product,
                        version=version,
                        serial_number=serial_number,
                        friendly_name=friendly_name,
                        parent_prefix_id=parent_prefix_id
                    )
                    usb_devices.append(usb_device)
            return usb_devices
        def __set_vendor_and_product_ids(self, usb_devices: List[USBDeviceWindows]) -> None:
            root_key = winreg.OpenKey(self.__machine_registry, WindowsViewer.__USB_PATH)
            device_ids = self.__get_registry_keys(root_key)
            device_dict = {}
            for device_id in device_ids:
                if 'VID' not in device_id or 'PID' not in device_id:
                    continue
                device_key = winreg.OpenKey(self.__machine_registry, rf'{WindowsViewer.__USB_PATH}\{device_id}')
                serial_number = self.__get_registry_keys(device_key)[0]
                device_dict[serial_number] = device_id
            for device in usb_devices:
                for serial_number, device_id in device_dict.items():
                    if device.serial_number != serial_number:
                        continue
                    device_info = device_id.split('&')
                    device.vendor_id = device_info[0].replace('VID_', '')
                    device.product_id = device_info[1].replace('PID_', '')
        def __set_guids(self, usb_devices: List[USBDeviceWindows]) -> None:
            root_key = winreg.OpenKey(self.__machine_registry, WindowsViewer.__MOUNTED_DEVICES_PATH)
            registry_values = self.__get_registry_values(root_key)
            for device in usb_devices:
                for key, value in registry_values.items():
                    value = convert_binary_to_ascii_string(value)
                    if device.parent_prefix_id not in value:
                        continue
                    if r'\Volume' in key:
                        guid_start_index = key.index('{')
                        device.guid = key[guid_start_index:]
        def __set_drive_letters(self, usb_devices: List[USBDeviceWindows]) -> None:
            root_key = winreg.OpenKey(self.__machine_registry, WindowsViewer.__PORTABLE_DEVICES_PATH)
            registry_keys = self.__get_registry_keys(root_key)
            for device in usb_devices:
                for key in registry_keys:
                    if device.parent_prefix_id not in key:
                        continue
                    device_key = winreg.OpenKey(self.__machine_registry, rf'{WindowsViewer.__PORTABLE_DEVICES_PATH}\{key}')
                    values = self.__get_registry_values(device_key)
                    device.drive_letter = values['FriendlyName']
        @staticmethod
        def __set_first_connect_dates(usb_devices: List[USBDeviceWindows]) -> None:
            time_dict = {}
            for log_path in glob.glob(r'C:\Windows\inf\setupapi.dev*.log'):  # There could be multiple files in system
                for section in parse_windows_log_file(log_path):
                    if 'Device Install ' in section[0] and 'SUCCESS' in section[-1]:
                        install_time = section[-2].split()[-2:]  # Get only date and time from string
                        install_time = ' '.join(install_time)
                        install_time = install_time.split('.')[0]  # Remove milliseconds
                        install_time = datetime.strptime(install_time, '%Y/%m/%d %H:%M:%S')
                        time_dict[section[0]] = install_time
            for device in usb_devices:
                for key, install_time in time_dict.items():
                    if device.serial_number in key:
                        device.first_connect_date = install_time
        def __set_last_connect_dates(self, usb_devices: List[USBDeviceWindows]) -> None:
            root_key = winreg.OpenKey(self.__user_registry, WindowsViewer.__MOUNT_POINTS_PATH)
            guids = self.__get_registry_keys(root_key)
            for device in usb_devices:
                for guid in guids:
                    if device.guid != guid:
                        continue
                    device_key = winreg.OpenKey(self.__user_registry, rf'{WindowsViewer.__MOUNT_POINTS_PATH}\{guid}')
                    timestamp = self.__get_registry_timestamp(device_key)
                    device.last_connect_date = datetime.fromtimestamp(timestamp)
        @staticmethod
        def __parse_device_name(device_name: str) -> Optional[Tuple[str, str, str]]:
            name_split = device_name.split('&')
            if len(name_split) != 4 or name_split[0] != 'Disk':
                return None
            vendor = name_split[1].replace('Ven_', '')
            product = name_split[2].replace('Prod_', '')
            version = name_split[3].replace('Rev_', '')
            return vendor, product, version
        @staticmethod
        def __get_registry_keys(root_key: winreg.HKEYType) -> List[str]:
            key_info = winreg.QueryInfoKey(root_key)
            keys_length = key_info[0]
            return [winreg.EnumKey(root_key, index) for index in range(keys_length)]
        @staticmethod
        def __get_registry_values(root_key: winreg.HKEYType) -> Dict[str, Any]:
            key_info = winreg.QueryInfoKey(root_key)
            values_length = key_info[1]
            values_dict = defaultdict(lambda: None)
            for index in range(values_length):
                name, value, _ = winreg.EnumValue(root_key, index)
                values_dict[name] = value
            return values_dict
        @staticmethod
        def __get_registry_timestamp(root_key: winreg.HKEYType) -> int:
            key_info = winreg.QueryInfoKey(root_key)
            return convert_windows_time_to_unix(key_info[2])


'''
LinuxViewer class extends BaseViewer. It provides an implementation of the get_usb_devices()
method, which returns a list of USBDeviceLinux objects representing the USB devices connected to the Linux system.
The implementation of get_usb_devices() method first gets a list of log sections containing information about
USB devices connected to the system. It then iterates over these sections and extracts relevant information
about each USB device, such as its vendor ID, product ID, version, serial number, and size.
The LinuxViewer class also contains several helper methods for parsing the log files and extracting information
about USB devices. These include methods for getting the last modification year of a log file, extracting the
device ID based on a given type (such as vendor or product ID), and getting the device size.
'''
# Main code for Linux systems that parsing  system's log files and collecting information
if platform.system() == 'Linux' :
    class LinuxViewer(BaseViewer):
        def __init__(self):
            self.__hostname = platform.node()
        def get_usb_devices(self) -> List[USBDevice]:
            usb_devices = self.__get_base_device_info()
            self._set_devices_info(usb_devices)
            return usb_devices
        def __get_base_device_info(self) -> List[USBDeviceLinux]:
            usb_devices = []
            for section, year in self.__get_log_sections():
                serial_number = self.__get_device_info_from_section(section, 'SerialNumber:')
                connect_time = self.__get_device_connect_time(section[0], year)
                device = self.__get_device_if_exist(usb_devices, serial_number)
                if device is not None:
                    device.last_connect_date = connect_time
                    continue
                device = USBDeviceLinux(serial_number=serial_number, first_connect_date=connect_time, last_connect_date=connect_time)
                device.vendor_id = self.__get_device_id_by_type(section[0], 'idVendor')
                device.product_id = self.__get_device_id_by_type(section[0], 'idProduct')
                device.version = self.__get_device_id_by_type(section[0], 'bcdDevice')
                device.syslog_product = self.__get_device_info_from_section(section, 'Product:')
                device.syslog_manufacturer = self.__get_device_info_from_section(section, 'Manufacturer:')
                device.serial_number = self.__get_device_info_from_section(section, 'SerialNumber:')
                device.friendly_name = self.__get_device_info_from_section(section, 'Direct-Access')
                device.device_size = self.__get_device_size(section)
                usb_devices.append(device)
            return usb_devices
        def __get_log_sections(self) -> Iterator[Tuple[List[str], int]]:
            for log_path in sorted(glob.glob('/var/log/syslog*'), reverse=True):
                year = self.__get_file_last_modification_year(log_path)
                for section in parse_linux_log_file(log_path):
                    yield section, year
        @staticmethod
        def __get_file_last_modification_year(filepath: str) -> int:
            timestamp = os.stat(filepath).st_mtime
            return datetime.fromtimestamp(timestamp).year
        def __get_device_connect_time(self, string: str, year: int) -> datetime:
            end_index = string.index(self.__hostname)
            connect_time = string[:end_index].strip()
            connect_time = f'{year}-{connect_time}'
            return datetime.strptime(connect_time, '%Y-%b %d %H:%M:%S')
        @staticmethod
        def __get_device_id_by_type(string: str, id_type: str) -> str:
            index_start = string.index(id_type)
            if ',' in string[index_start:]:
                index_end = string.index(',', index_start)
            else:
                index_end = len(string)
            device_id = string[index_start:index_end]
            device_id = device_id.replace(f'{id_type}=', '')
            device_id = device_id.strip()
            return device_id
        @staticmethod
        def __get_device_info_from_section(section: List[str], info_type: str) -> Optional[str]:
            for line in section:
                if info_type in line:
                    start_index = line.index(info_type)
                    return line[start_index + len(info_type):].split(maxsplit=1)[-1].strip()
            return None
        @staticmethod
        def __get_device_size(section: List[str]) -> Optional[str]:
            for line in section:
                if 'logical blocks' in line:
                    index_start = line.rindex(']')
                    return line[index_start + 1:].strip()
            return None
        @staticmethod
        def __get_device_if_exist(usb_devices: List[USBDeviceLinux], serial_number: str) -> Optional[USBDeviceLinux]:
            for device in usb_devices:
                if device.serial_number == serial_number:
                    return device
            return None

'''
get_usb_viewer() is the main driver function that returns an instance of a BaseViewer subclass depending on the
current operating system.
If the current operating system is Windows, it creates an instance of WindowsViewer, which is a subclass of
BaseViewer. If the current operating system is Linux, it creates an instance of LinuxViewer, which is another
subclass of BaseViewer. If the operating system is neither Windows nor Linux, it returns None.
The function has a return type annotation of Optional[BaseViewer], which indicates that it can return
either an instance of BaseViewer or None.
'''
def get_usb_viewer() -> Optional[BaseViewer]:
    if platform.system() == 'Windows':
        return WindowsViewer()
    elif platform.system() == 'Linux':
        return LinuxViewer()
    else:
        return None

def terminal_banner():
    main_str= "                                                            "
    text = "Developed By : Hrishikesh Patra (Hrishikesh7665)"
    text1 = "Version : " + __version__
    new_string = main_str[len(text):]
    new_string1 = main_str[len(text1):]
    dev_name = str(new_string[ : len(new_string)//2] + text + new_string[len(new_string)//2 : ])
    version  = str(new_string1[ : len(new_string1)//2] + text1 + new_string1[len(new_string1)//2 : ])+"\n"
    os.system('cls')
    print(ascii_col,end='')
    print(main_str)
    print(' ██████╗  █████╗ ███████╗████████╗ ██╗   ██╗███████╗██████╗ ')
    print(' ██╔══██╗██╔══██╗██╔════╝╚══██╔══╝ ██║   ██║██╔════╝██╔══██╗')
    print(' ██████╔╝███████║███████╗   ██║    ██║   ██║███████╗██████╔╝')
    print(' ██╔═══╝ ██╔══██║╚════██║   ██║    ██║   ██║╚════██║██╔══██╗')
    print(' ██║     ██║  ██║███████║   ██║    ╚██████╔╝███████║██████╔╝')
    print(' ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝     ╚═════╝ ╚══════╝╚═════╝ ')
    print (dev_name)
    print (version)

if __name__ == '__main__':
    os.system("")
    terminal_banner()
    if platform.system() == 'Windows':
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print(light_red,end='')
                print('[×] Administrator rights not found')
                print(yellow,end='')
                print('[*] Please run this script as Administrator')
                print(nocolor,end='')
                exit()
            else:
                print(green,end='')
                print('[√] Administrator rights are granted')
        except Exception as e:
            print(red,end='')
            print('[!!!] Error while checking permissions')
            print('Debug :',e)
            print(nocolor,end='')
            exit()
    elif platform.system() == 'Linux':
        if os.geteuid() != 0:
            print(light_red,end='')
            print('[×] sudo permission denied')
            print(yellow,end='')
            print('[*] Please run this script as root')
            print(nocolor,end='')
            exit()
        else:
            print(green,end='')
            print('[√] sudo permission granted')
    else:
        print(red,end='')
        print('Sorry!! This script is only for Windows and Linux')
        print(nocolor,end='')
        exit()
    viewer = get_usb_viewer()
    devices = viewer.get_usb_devices()
    print(yellow,end='')
    if (len(devices)) == 1:
        print('[!] 1 USB Device found in history')
    elif (len(devices)) >= 2 :
        print('[!] '+str(len(devices))+' USB Devices found in history')
    else:
        print('[!] No USB Device found in history')
        print(nocolor,end='')
        exit()
    print(log_col)
    for device in devices:
        print(device.get_details())
    print(nocolor,end='')
else:
    def PastUSB ():
        if platform.system() == 'Windows':
            if not ctypes.windll.shell32.IsUserAnAdmin():
                raise Exception("Administrator rights not found")
        elif platform.system() == 'Linux':
            if os.geteuid() != 0:
                raise Exception("sudo permission denied")
        else:
            raise Exception("Unsupported platform detected")
        viewer = get_usb_viewer()
        devices = viewer.get_usb_devices()
        return devices