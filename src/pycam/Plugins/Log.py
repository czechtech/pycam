# -*- coding: utf-8 -*-
"""
$Id$

Copyright 2011 Lars Kruse <devel@sumpfralle.de>

This file is part of PyCAM.

PyCAM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PyCAM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PyCAM.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import datetime

import pycam.Plugins


class Log(pycam.Plugins.PluginBase):

    UI_FILE = "log.ui"

    def setup(self):
        if self.gui:
            import gtk
            self._gtk = gtk
            # menu item and shortcut
            actiongroup = self._gtk.ActionGroup("log")
            log_action = self.gui.get_object("ToggleLogWindow")
            log_action.connect("toggled", self.toggle_log_window)
            key, mod = self._gtk.accelerator_parse("<Control>l")
            # TODO: move the "<pycam>" accel path somewhere else
            accel_path = "<pycam>/ToggleLogWindow"
            log_action.set_accel_path(accel_path)
            self._gtk.accel_map_change_entry(accel_path, key, mod, True)
            actiongroup.add_action(log_action)
            self.core.get("gtk-uimanager").insert_action_group(actiongroup, pos=-1)
            # status bar
            self.status_bar = self.gui.get_object("StatusBar")
            self.gui.get_object("StatusBarEventBox").connect("button-press-event",
                    self.toggle_log_window)
            event_bar = self.gui.get_object("StatusBarEventBox")
            event_bar.unparent()
            self.core.register_ui("main_window", "Status", event_bar, 100)
            # "log" window
            self.log_window = self.gui.get_object("LogWindow")
            self.log_window.set_default_size(500, 400)
            self.log_window.connect("delete-event", self.toggle_log_window, False)
            self.log_window.connect("destroy", self.toggle_log_window, False)
            self.gui.get_object("LogWindowClose").connect("clicked", self.toggle_log_window, False)
            self.gui.get_object("LogWindowClear").connect("clicked", self.clear_log_window)
            self.gui.get_object("LogWindowCopyToClipboard").connect("clicked",
                    self.copy_log_to_clipboard)
            self.log_model = self.gui.get_object("LogWindowList")
            # window state
            self._log_window_position = None
            # register a callback for the log window
            pycam.Utils.log.add_hook(self.add_log_message)
        return True

    def add_log_message(self, title, message, record=None):
        timestamp = datetime.datetime.fromtimestamp(
                record.created).strftime("%H:%M")
        # avoid the ugly character for a linefeed
        message = " ".join(message.splitlines())
        try:
            message = message.encode("utf-8")
        except UnicodeDecodeError:
            # remove all non-ascii characters
            clean_char = lambda c: (32 <= ord(c) < 128) and c or " "
            message = "".join([clean_char(char) for char in message])
        self.log_model.append((timestamp, title, message))
        # update the status bar (if the GTK interface is still active)
        if not self.status_bar.window is None:
            # remove the last message from the stack (probably not necessary)
            self.status_bar.pop(0)
            # push the new message
            try:
                self.status_bar.push(0, message)
            except TypeError:
                new_message = re.sub("[^\w\s]", "", message)
                self.status_bar.push(0, new_message)
            # highlight the "warning" icon for warnings/errors
            if record and record.levelno > 20:
                self.gui.get_object("StatusBarWarning").show()

    def copy_log_to_clipboard(self, widget=None):
        content = []
        def copy_row(model, path, it, content):
            columns = []
            for column in range(model.get_n_columns()):
                columns.append(model.get_value(it, column))
            content.append(" ".join(columns))
        self.log_model.foreach(copy_row, content)
        self.clipboard.set_text(os.linesep.join(content))
        self.gui.get_object("StatusBarWarning").hide()

    def clear_log_window(self, widget=None):
        self.log_model.clear()
        self.gui.get_object("StatusBarWarning").hide()

    def toggle_log_window(self, widget=None, value=None, action=None):
        toggle_log_checkbox = self.gui.get_object("ToggleLogWindow")
        checkbox_state = toggle_log_checkbox.get_active()
        if value is None:
            new_state = checkbox_state
        elif isinstance(value, self._gtk.gdk.Event):
            # someone clicked at the status bar -> toggle the window state
            new_state = not checkbox_state
        else:
            if action is None:
                new_state = value
            else:
                new_state = action
        if new_state:
            if self._log_window_position:
                self.log_window.move(*self._log_window_position)
            self.log_window.show()
        else:
            self._log_window_position = self.log_window.get_position()
            self.log_window.hide()
        toggle_log_checkbox.set_active(new_state)
        self.gui.get_object("StatusBarWarning").hide()
        # don't destroy the window with a "destroy" event
        return True

