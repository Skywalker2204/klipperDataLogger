# klipperDataLogger
## General Information and Installation
This is a plugin for klipper, to add the function of writing a log file recording the extruder temprature, heated bed temperture and filament width data, by default. The data are stored in an string array and can be saved to a Text file. To make use of the plugin put the file_writer.py file in the klippy/extras directory and compile the file by enter following command:
```
python -m compileall file_writer.py
```
## Initialisation
To enable the plugin ist has to be declaired in the pinter.cfg or similar file and suppyl the diractory to save the output file. 
```
[file_writer]
path: ~\source
```
## Commands
The plugin is then running in the background and can be enabled by GCode commands build in the function. It can be enabled and disabled by the folloing commands, note that logging is only performed during printing!!!
```
DATA_LOGGING_ENABLE
DATA_LOGGING_DISABLE
```
By default the printing time, extrustion temperature, heated bed temperature is logged but any existing value, avaliable by the get_status(eventtime) by making use of the implemented command:
```
DATA_LOGGING_ADD_VALUE VALUE=virtual_sdcard.progress
```
The data are stored in a local variable and can be saved by add in the command. By default the file name is the same as the printed Gcode replaced by the .out ending, if none filename is found "default.out" is used. Another filename can be passed if needed.
```
DATA_LOGGING_SAVE FILENAME=myName.out
```
The cache text array can be cleard by using ```DATA_LOGGING_CLEAR```.
## Comments
The plugin is still under development and any issue will be solved as fast as possible
