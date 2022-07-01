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
        self.name=config.get_name().split()[-1]
        #get objects
        self.sd = self.printer.load_object(config, 'virtual_sdcard')
        self.print_stats = self.printer.load_object(config, 'print_stats')
        #internal Variables !!!Dont use global variables!!!!!
        self.path = os.path.expanduser(config.get('path'))
        self.is_active = False
        self.behaviour = 'pritning'
        self.is_log = config.getboolean('debug',False)
        self.values = list(config.getlists('values', seps=(',','\n')))
                                     #[object, value]
        self.eventtime = self.reactor.NEVER
        self.text = []
        self.duration = 0.
        #register the event handler
        self.logger_update_timer = self.reactor.register_timer(
            self._logger_event)
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
    def _lookup_object(self, obj):
        po = self.printer.lookup_object(obj, None)
        if po is None or not hasattr(po, 'get_status'):
            raise KeyError(obj)
        return po
    #Construction of the line
    def _write_values(self, eventtime, delimiter='\t'):
        pd = self.print_stats.get_status(eventtime)['print_duration']
        if pd or self.behaviour=='all':
            line = '\n' + str(pd) + delimiter
            for obj, value in self.values:
                po = self._lookup_object(obj)
                try:
                    line += str(po.get_status(eventtime)[value])+delimiter
                except Exception as e:
                    line += str(e)+delimiter
            if self.is_log: self.gcode.respond_info(line)
            self.text.append(line)
    #Constructor for the Header
    def _write_header(self, delimiter='\t'):
        header = 'time'+delimiter
        for obj, value in self.values:
            header += obj + " " + value + delimiter
        self.text.append(header)
    #file write method
    def _save_to_file(self,filename):
        if len(self.text)==0:
            self.gcode.respond_info("Nothing to save!")
        else:
            self.gcode.respond_info(str(os.path.join(self.path, filename)))
            try:
                f = open(os.path.join(self.path, filename), 'a')
                f.writelines(self.text)
                f.close()
            except Exception as e:
                self.gcode.respond_info("Error: " + e)
    #Main event running
    def _logger_event(self, eventtime):
        nextwake = self.reactor.NEVER
        if self.is_active:
            if self.is_log:
                self.gcode.respond_info(
                    "Now the Data logger is active: "+ str(eventtime))
            if self.print_stats.get_status(eventtime)['state']=='printing':
                if len(self.text)==0: self._write_header()
                self._write_values(eventtime)
            nextwake = eventtime + self.duration
        return nextwake
    #Definition of Commands
    def cmd_log_enable(self, gcmd):
        self.is_active=True
        self.duration=gcmd.get_float('DURATION', default=1., minval=0.)
        self.behaviour= gcmd.get('BEHAVIOUR', default=self.behaviour)
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
        self.values.append([obj,value])
        text=''
        if self.is_log:
            for obj, val in self.values:
                text += ' '+obj+' '+val
        gcmd.respond_info("Added Value for logging"+self.name+text)
    def cmd_clear(self, gcmd):
        self.text = []
        gcmd.respond_info("Cleared data in the cache")
    def cmd_save(self, gcmd):
        fn = gcmd.get('FILENAME', None)
        if fn is None:
            fn=self.print_stats.get_status(
                self.reactor.NOW)['filename']
            try:
                fn = fn.replace('.gcode', '_log.out')
            except Exception as e:
                fn = 'default.out'
                self.gcode.respond_info('Filename not found use default' + e)
        try:
            self._save_to_file(fn)
        except Exception as e:
            raise e
        gcmd.respond_info("Sucessfully worte to file " + fn)
    #Add a status variable
    def get_status(self, eventtime):
        return {'is_active':self.is_active,
                'cache_text':self.text, 
                'values':self.values}

def load_config_prefix(config):
    return fileWriter(config)
