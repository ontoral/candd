#! /usr/bin/env python
import os
import sys
import datetime

import wx
from wx.lib.calendar import Calendar
from wx.lib.filebrowsebutton import DirBrowseButton, FileBrowseButton
import wx.gizmos as gizmos

import pricer


class Blocker(object):
    """Context handler for blocking events from programmatic changes.

    usage:
        blocking = Blocker()        # blocking is False by default

        blocking == False
        with blocking:
            blocking == True
        blocking == False

        def some_func():
            if blocking:
                return
            with blocking:
                some_func()         # blocking prevents recursion
    """
    def __init__(self):
        self._blocker = False

    def __nonzero__(self):
        return self._blocker

    def __enter__(self):
        self._blocker = True

    def __exit__(self, type, value, traceback):
        self._blocker = False


class MainFrame(wx.Frame):
    def _init_ctrls(self, parent):
        self.DecYear = wx.Button(self, -1, '<<', size=(48, 36))
        self.DecYear.Bind(wx.EVT_BUTTON, self.OnDecYear)
        self.DecMonth = wx.Button(self, -1, ' < ', size=(48, 36))
        self.DecMonth.Bind(wx.EVT_BUTTON, self.OnDecMonth)
        self.Current = wx.Button(self, -1, 'Today')
        self.Current.Bind(wx.EVT_BUTTON, self.OnCurrent)
        self.IncMonth = wx.Button(self, -1, ' > ', size=(48, 36))
        self.IncMonth.Bind(wx.EVT_BUTTON, self.OnIncMonth)
        self.IncYear = wx.Button(self, -1, '>>', size=(48, 36))
        self.IncYear.Bind(wx.EVT_BUTTON, self.OnIncYear)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        bsizer.Add(self.DecYear, 0, wx.ALL, 2)
        bsizer.Add(self.DecMonth, 0, wx.ALL, 2)
        bsizer.Add(self.Current, 1, wx.ALL | wx.EXPAND, 2)
        bsizer.Add(self.IncMonth, 0, wx.ALL, 2)
        bsizer.Add(self.IncYear, 0, wx.ALL, 2)

        self.Calendar = Calendar(self, -1, size=(200, 300))
        self.Calendar.Bind(wx.lib.calendar.EVT_CALENDAR, self.OnCalendarChange)
        self.Calendar.SetCurrentDay()
        self.Calendar.grid_color = 'BLUE'
        self.Calendar.SetBusType()

        self.FBB = FileBrowseButton(self, size=(450, -1), changeCallback=self.OnFBBChange)
        self.FBB.SetLabel('Symbols File:')

        self.DBB = DirBrowseButton(self, size=(450, -1), changeCallback=self.OnDBBChange)
        self.DBB.SetLabel('Prices Folder:')

        self.ListBox = gizmos.EditableListBox(self, -1,
#              style=gizmos.EL_DEFAULT_STYLE | gizmos.EL_NO_REORDER
               )
        self.ListBox.GetUpButton().Show(False)
        self.ListBox.GetDownButton().Show(False)
        self.ListBox.Bind(wx.EVT_LIST_DELETE_ITEM, self.OnSymbolListChange)
        self.ListBox.Bind(wx.EVT_LIST_INSERT_ITEM, self.OnSymbolListChange)

        self.Download = wx.Button(self, wx.OK, 'Download Prices')
        self.Download.Bind(wx.EVT_BUTTON, self.OnDownload)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSizer(bsizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.AddWindow(self.Calendar, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.AddWindow(self.FBB, 0, wx.ALL | wx.EXPAND, 5)
        sizer.AddWindow(self.DBB, 0, wx.ALL | wx.EXPAND, 5)
        sizer.AddWindow(self.ListBox, 1, wx.ALL | wx.EXPAND, 5)
        sizer.AddWindow(self.Download, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.SetSizer(sizer)

    def __init__(self, parent=None):
        wx.Frame.__init__(self, parent=parent, size=(800, 600))
        self._init_ctrls(self)

        self._blocking = Blocker()
        self._clean = True

        # Get download directory and symbol filename
        download_dir = ''
        symbol_file = ''

        if os.path.exists('settings.ini'):
            with file('settings.ini', 'r') as settings:
                symbol_file = settings.readline().strip()
                download_dir = settings.readline().strip()
            if not os.path.exists(symbol_file):
                symbol_file = ''
            if not os.path.exists(download_dir):
                download_dir = ''

        download_dir = download_dir or os.path.realpath('.')
        symbol_file = symbol_file or os.path.join(download_dir, 'symbols.txt')

        self.SetDownloadDir(download_dir)
        if os.path.exists(symbol_file):
            self.SetSymbolFile(symbol_file)

        # Update the calendar
        self.Download.SetFocus()
        self.OnCalendarChange(None)

    def OnCalendarChange(self, event):
        self.day = self.Calendar.day
        self.month = self.Calendar.month
        self.year = self.Calendar.year

    def OnCurrent(self, event):
        self.Calendar.SetCurrentDay()
        self.ResetDisplay()

    def OnDBBChange(self, event):
        if self._blocking:
            return
        self.SetDownloadDir(event.GetString())

    def OnDecMonth(self, event):
        self.Calendar.DecMonth()
        self.ResetDisplay()

    def OnDecYear(self, event):
        self.Calendar.DecYear()
        self.ResetDisplay()

    def OnDownload(self, event):
        if not self._clean:
            with file(self.symbol_file, 'w') as symbols:
                symbols.write('\n'.join(self.ListBox.GetStrings()))
            self._clean = True

        pricer.get_quotes(self.month, self.day, self.year,
                          self.symbol_file, self.download_dir)

        with file('settings.ini', 'w') as settings:
            settings.write(self.symbol_file + '\n')
            settings.write(self.download_dir + '\n')

    def OnFBBChange(self, event):
        if self._blocking:
            return
        self.ListBox.SetStrings([])
        self.SetSymbolFile(event.GetString())

    def OnIncMonth(self, event):
        self.Calendar.IncMonth()
        self.ResetDisplay()

    def OnIncYear(self, event):
        self.Calendar.IncYear()
        self.ResetDisplay()

    def OnSymbolListChange(self, event):
        self._clean = False
        self.Download.Enable(len(self.ListBox.GetStrings()) > 0)

    def ResetDisplay(self):
        self.Calendar.Refresh()

    def SetDownloadDir(self, download_dir):
        with self._blocking:
            self.download_dir = download_dir
            self.DBB.SetValue(self.download_dir)

    def SetSymbolFile(self, symbol_file):
        self.Download.Enable(False)
        with self._blocking:
            if not os.path.exists(symbol_file):
                return
            self.symbol_file = symbol_file

            with file(self.symbol_file, 'r') as symbols:
                l = []
                for symbol in symbols:
                    s = symbol.strip().upper()
                    if len(s) and not s.startswith('#'):
                        l.append(s)
                l.sort()
                self.ListBox.SetStrings(l)
                self._clean = True
            self.FBB.SetValue(self.symbol_file)


class SupplementalPricesApp(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        main_frame = MainFrame()
        main_frame.Show()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == 'daily':
            dt = datetime.date.today()
            symbol_file = os.path.join('..', 'symbols.txt')
            download_dir = os.path.join('..', 'supplemental-prices')
            pricer.get_quotes(dt.month, dt.day, dt.year, symbol_file, download_dir)
    else:
        app = SupplementalPricesApp()
        app.MainLoop()
