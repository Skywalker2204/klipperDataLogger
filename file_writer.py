#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 03:38:21 2022

@author: lukashentschel
"""

import logging, os

class fileWriter:
    def __init__(self, config):
        self.printer=config.get_printer()
        self.reactor = self.printer.get_reactor()
        #get objects
        self.sd = self.printer.load_object(config, 'virtual_sdcard')
        self.print_stats = self.printer.load_object(config, 'print_stats')
        #internal Variables !!!Dont use global variables!!!!!
        self.is_active = False
        self.is_log = True
        self.values = {'extruder' : 'tempeature',
                       'bed' : 'temperature',
                       'optical_filament_width_sensor':'diameter'}
        self.eventtime = None
        self.text = ''
        self.duration = 0.
        #register the event handler
        self.logger_update_timer = self.reactor.register_timer(
            self._logger_event())
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        #Register commands
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command("DATA_LOGGING_ENABLE",
                                    self.cmd_log_enable)
        self.gcode.register_command("DATA_LOGGING_DISABLE",
                                    self.cmd_log_disable)
        self.gcode.register_command("DATA_LOGGING_ADD_VALUE",
                                    self.cmd_add_value)
        self.gcode.register_command("DATA_LOGGING_CLEAR",
                                    self.cmd_clear)
        self.gcode.register_command("DATA_LOGGING_SAVE",
                                    self.cmd_save)
    def _handle_ready(self):
        waketime = self.reactor.NEVER
        if self.duration:
            waketime = self.reactor.monotonic() + self.duration
        self.reactor.update_timer(
            self.logger_update_timer, waketime)
        pass
    #look p for values
    def _lookup_objects(self, obj):
        po = self.printer.lookup_object(obj, None)
        if po is None or not hasattr(po, 'get_status'):
            raise KeyError(obj)
        return po
    #Construction of the line
    def _write_values(self, delimiter='\t'):
        line = '\n'+self.print_stats.get_status(
            self.eventtime)['print_duration']+delimiter
        if len(self.objs) == 0: self.lookup_objects()
        for obj, value in self.values:
            po = self._lookup_objects(obj)
            try:
                for val in value:
                    line += "{:.3f}".format(po.get_status()[val])+delimiter
            except TypeError:
                line += "{:.3f}".format(po.get_status()[value])+delimiter
            except Exception as e:
                line += 'nan'+delimiter
        if self.is_log: logging.info(line)
        self.text += line
    #Constructor for the Header
    def _write_header(self, delimiter='\t'):
        for obj, value in self.values():
            header = 'time'+delimiter
            try:
                for i in value:
                    header += obj +" " + i + delimiter
                    pass
            except TypeError:
                self.header += obj +" " + value + delimiter
            self.text = header
    #file write method
    def _save_to_file(self, filename):
        with open(os.path.join(self.path, filename), 'a') as file:
            file.write(self.text)
        pass
    #Main event running
    def _logger_event(self, eventtime):
        nextwake = self.reactor.NEVER
        if self.is_active:
            if self.is_log:logging.info(
                    "Now the Data logger is active: ", str(eventtime))
            if self.sd.get_status(eventtime)['is_active']:
                if self.text == '': self._write_header()
                self._write_values() 
            nextwake = eventtime + self.duration
        return nextwake
    #Definition of Commands
    def cmd_log_enable(self, gcmd):
        self.is_active=True
        self.duration=gcmd.get_float('DURATION', default=1., minval=0.)
        self.reactor.update_timer(
            self.logger_update_timer, self.reactor.NOW)
        gcmd.respond_info("Data logging is enabled")
        pass
    def cmd_log_disable(self, gcmd):
        self.is_active=False
        self.reactor.update_timer(
            self.logger_update_timer, self.reactor.NEVER)
        gcmd.respond_info("Data logging is disabled")
        pass
    def cmd_add_value(self, gcmd):
        raw_input = gcmd.get('VALUE', default=None)
        if  not raw_input:
            gcmd.respond_info("No object is given in VALUE!")
            return
        try:
            obj, value = raw_input.split('.')
        except Exception as e:
            if self.is_log: logging.info(e)
            gcmd.respond_info("Wrong format of input! Try obj.value")
        po = self.printer.lookup_object(obj, None)
        if po is None or not hasattr(po, 'get_status'):
            raise KeyError(obj) 
        self.values.update({obj:value})
        gcmd.respond_info("Added Value for logging")
    def cmd_clear(self, gcmd):
        self.text = ''
        gcmd.responde_info("Cleared data in the cache")
    def cmd_save(self, gcmd):
        fn = gcmd.get('FILENAME', None)
        if fn==None: fn=self.st.get_status(
                self.eventtime)['filename'].replace('.gcode', '_log.out')
        try:
            self._save_to_file(fn)
        except Exception as e:
            raise e
        gcmd.responde_info("Sucessfully worte to file " + fn) 
    #Add a status variable
    def get_status(self, eventtime):
        return {'is_active':self.is_active, 
                'cache_text':self.text}

def load_config(config):
    return fileWriter(config)
