#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 03:38:21 2022

@author: lukashentschel
"""

import logging, copy
import os

# Wrapper for access to printer object get_status() methods
class GetStatusWrapper:
    def __init__(self, printer, eventtime=None):
        self.printer = printer
        self.eventtime = eventtime
        self.cache = {}
    def __getitem__(self, val):
        sval = str(val).strip()
        if sval in self.cache:
            return self.cache[sval]
        po = self.printer.lookup_object(sval, None)
        if po is None or not hasattr(po, 'get_status'):
            raise KeyError(val)
        if self.eventtime is None:
            self.eventtime = self.printer.get_reactor().monotonic()
        self.cache[sval] = res = copy.deepcopy(po.get_status(self.eventtime))
        return res
    def __contains__(self, val):
        try:
            self.__getitem__(val)
        except KeyError as e:
            return False
        return True
    def __iter__(self):
        for name, obj in self.printer.lookup_objects():
            if self.__contains__(name):
                yield name

class fileWriter:
    def __init__(self, config):
        self.printer=config.get_printer()
        
        # Print Stat Tracking
        self.wrapper = GetStatusWrapper()
        
        self.is_Printing = 'printing' in self.wrapper['print_stats']['state']
        self.path = self.wrapper['virtual_sdcard']['file_path']

        self.is_Active = False
        
        self.values = {'extruder' : 'tempeature', 
                       'bed' : 'temperature', 
                       'optical_filament_width_sensor':'diameter'}
        self.header = ''
        self.filename=''
        
        #Register commands
        gcode = self.printer.lookup_object('gcode')
        gcode.register_command("DATA_LOGGING_ENABLE", self.cmd_log_enable())        
        gcode.register_command("DATA_LOGGING_DISABLE", self.cmd_log_disable())        
        gcode.register_command("DATA_LOGGING_ADD_VALUE", self.cmd_add_value())
    
    # Constructor of the text line           
    def _write_values(self, delimiter='\t'):
        line = '\n'+self.wrapper['print_stats']['print_duration']+delimiter
        for obj, value in self.values():
            try:
                for val in value:
                    line += "{:.3f}".format(self.wrapper[obj][val])+delimiter
            except TypeError:                
                line += "{:.3f}".format(self.wrapper[obj][value])+delimiter
        self._write_line(line)        
        pass
    #Constructor for the Header
    def _write_header(self, delimiter='\t'):
        for obj, value in self.values():
            self.header = 'time'+delimiter
            try:
                for i in value:
                    self.header += obj +" " + i + delimiter
                    pass
            except TypeError:
                self.header += obj +" " + value + delimiter
            self._write_line(self.header)
        return self.header
    #file write method
    def _write_line(self, text):
        with open(os.path.join(self.path, self.filename), 'a') as file:
            file.write(text)
        pass
    #Main event running    
    def logger_event(self, eventtime):
        if self.is_Active() and self.is_Printing:
            if self.filename=='':
                self.filename = self.wrapper['print_stats']['filename'].replace('.gcode', '_log.out')
            if self.header == 0: self._write_header()
            self._write_values()
    #Definition of Commands
    def cmd_log_enable(self, gcmd):
        self.is_Active=True
        gcmd.respond_info("Data logging is enabled")
        pass
    
    def cmd_log_disable(self, gcmd):
        self.is_Active=False
        gcmd.respond_info("Data logging is disabled")
        pass
    
    def cmd_add_value(self, gcmd):
        obj, value = gcmd.get('VALUE').split()
        if obj in self.wrapper: 
            self.values.update({obj:value})
            gcmd.respond_info("Added Value for logging")
        else:
            gcmd.respond_info("Value not found!")

    #Add a status variable
    def get_status(self, eventtime):
        return {'is_Active':self.is_Active}


def load_config(config):
    return fileWriter(config)