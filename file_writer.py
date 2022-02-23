#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 03:38:21 2022

@author: lukashentschel
"""

import logging, copy, os

class fileWriter:
    def __init__(self, config):
        self.printer=config.get_printer()
        #get objects
        self.stats = self.printer.load_object(config, 'print_stats')
        self.sd = self.printer.load_object(config, 'virtual_sd')
        #internal 
        self.is_active=False
        self.is_Printing = False
        self.path = None
        self.filename=''
        self.values = {'extruder' : 'tempeature',
                       'bed' : 'temperature',
                       'optical_filament_width_sensor':'diameter'}
        self.eventtime=None
        self.objs = {}
        self.text=''
        #Register commands
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command("DATA_LOGGING_ENABLE", self.cmd_log_enable)
        self.gcode.register_command("DATA_LOGGING_DISABLE", self.cmd_log_disable)
        self.gcode.register_command("DATA_LOGGING_ADD_VALUE", self.cmd_add_value)
    # Constructor of the text line
    def lookup_objects(self, config):
        for key, val in self.values.items():
            if self.objs[key]:
                self.gcode.responde_info('Object already loaded')
            else:
                self.objs[key]=self.printer.load_object(config, key)
    def _write_values(self, delimiter='\t'):
        line = '\n'+self.stats.get_status(self.eventtime)['print_duration']+delimiter
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
    def _write_to_file(self, text):
        with open(os.path.join(self.path, self.filename), 'a') as file:
            file.write(text)
        pass
    #Main event running
    def logger_event(self, eventtime):
        if self.is_active() and self.is_Printing:
            if self.filename=='':
                self.filename = self.wrapper['print_stats']['filename'].replace('.gcode', '_log.out')
            if self.header == 0: self._write_header()
            self._write_values()
    #Definition of Commands
    def cmd_log_enable(self, gcmd):
        self.is_active=True
        gcmd.respond_info("Data logging is enabled")
        pass

    def cmd_log_disable(self, gcmd):
        self.is_active=False
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
        return {'is_active':self.is_active}


def load_config(config):
    return fileWriter(config)
