import wx
import logging
import matplotlib.cm
import numpy as np
import properties

p = properties.Properties.getInstance()

slider_width = 30
s_off = slider_width/2

class ColorBarPanel(wx.Panel):
    '''
    A HORIZONTAL color bar and value axis drawn on a panel.
    '''
    def __init__(self, parent, map, local_extents=[0.,1.], global_extents=None, 
                 ticks=5, **kwargs):
        '''
        map -- a colormap name from matplotlib.cm
        local_extents -- local min and max values of the measurement
        global_extents -- min and max values of the measurement
        ticks -- # of ticks to display values for on the bar
                 1 or 0 will draw no ticks
        labelformat -- a valid format string for the values displayed
                       on the value axis 
        '''
        wx.Panel.__init__(self, parent, **kwargs)
        self.ticks = ticks
        self.labelformat = '%.3f'
        self.low_slider = wx.Button(self, -1, '[', pos=(0,-1), size=(slider_width,-1))
        self.high_slider = wx.Button(self, -1, ']', pos=(self.Size[0],-1), size=(slider_width,-1))
        self.ClearNotifyWindows()
        self.SetMap(map)
        self.interval = list(local_extents)
        self.local_extents = local_extents
        self.global_extents = list(local_extents)
        self.clipmode = 'rescale'
        
        self.low_slider.SetToolTipString('')
        self.low_slider.GetToolTip().Enable(True)
        
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.low_slider.Bind(wx.EVT_LEFT_DOWN, self.OnClipSliderLeftDown)
        self.low_slider.Bind(wx.EVT_MOTION, self.OnClipSliderMotion)
        self.high_slider.Bind(wx.EVT_LEFT_DOWN, self.OnClipSliderLeftDown)
        self.high_slider.Bind(wx.EVT_MOTION, self.OnClipSliderMotion)
        
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnLeftDown(self, evt):
        # Get the slider closest to the click point.
        if abs(self.low_slider.GetPositionTuple()[0] - evt.X) < abs(self.high_slider.GetPositionTuple()[0] - evt.X):
            self.cur_slider = self.low_slider
        else:
            self.cur_slider = self.high_slider
        self.cur_slider.SetPosition((evt.X - s_off, -1))
        self.xo = 0
        self.UpdateInterval()
    
    def OnMotion(self, evt):
        if not evt.Dragging() or not evt.LeftIsDown():
            return
        self.cur_slider.SetPosition((evt.X - s_off, -1))
        self.UpdateInterval()
    
    def OnClipSliderLeftDown(self, evt):
        self.cur_slider = evt.EventObject
        self.xo = evt.X
    
    def OnClipSliderMotion(self, evt):
        slider = evt.EventObject
        if not evt.Dragging() or not evt.LeftIsDown():
            return
        slider.SetPosition((slider.GetPositionTuple()[0] + evt.X - self.xo - s_off, -1))
        self.xo = 0
        self.UpdateInterval()
        
    def ClearNotifyWindows(self):
        self.notify_windows = []
    
    def AddNotifyWindow(self, win):
        self.notify_windows += [win]
    
    def ResetInterval(self):
        ''' Sets clip interval to the extents of the colorbar. '''
        self.interval = list(self.global_extents)
        self.low_slider.SetPosition((0-s_off,-1))
        self.high_slider.SetPosition((self.Size[0]-s_off,-1))
        for win in self.notify_windows:
            win.SetClipInterval(self.GetLocalInterval(), self.local_extents, self.clipmode)
        self.Refresh()
    
    def UpdateInterval(self):
        ''' Calculates the interval values w.r.t. the current extents
        and clipping slider positions. '''
        range = self.global_extents[1]-self.global_extents[0]
        w = float(self.Size[0])
        if range>0 and w>0:
            print self.global_extents
            self.interval[0] = self.global_extents[0] + ((self.low_slider.GetPositionTuple()[0] + s_off) / w * range)
            self.interval[1] = self.global_extents[0] + ((self.high_slider.GetPositionTuple()[0] + s_off) / w * range)
        
            self.low_slider.SetToolTipString(str(self.global_extents[0] + ((self.low_slider.GetPositionTuple()[0] + s_off) / w * range)))
            self.high_slider.SetToolTipString(str(self.global_extents[0] + ((self.high_slider.GetPositionTuple()[0] + s_off) / w * range)))
        else:
            self.interval = list(self.local_extents)
        
        self.UpdateLabelFormat()
        
        for win in self.notify_windows:
            win.SetClipInterval(self.GetLocalInterval(), self.local_extents, self.clipmode)
        self.Refresh()
        
# TODO: To be added.  Not sure how to treat intervals that are outside 
#       the current extents, do we resize the extents?  This could get
#       ugly and confusing.

#    def SetInterval(self, interval):
#        self.interval = interval
#        self.low_slider.SetPosition((0-s_off,-1))                
#        self.high_slider.SetPosition((self.Size[0]-s_off,-1))
#        for win in self.notify_windows:
#            win.SetClipInterval(self.GetInterval(), self.clipmode)
#        self.Refresh()
        
    def GetGlobalInterval(self):
        ''' Returns the interval clipped on the value axis. '''
        return self.interval
    
    def GetLocalInterval(self):
        ''' Returns the interval clipped on the local color bar. 
        If either part is outside the local_extents, the extent is returned.
        '''
        i = list(self.interval)
        if self.interval[0] < self.local_extents[0]:
            i[0] = self.local_extents[0]
        if self.interval[1] > self.local_extents[1]:
            i[1] = self.local_extents[1]
        return i
    
    def GetGlobalExtents(self):
        return self.global_extents
        
    def GetLocalExtents(self):
        return self.local_extents
    
    def GetClipMode(self):
        return self.clipmode
        
    def SetMap(self, map):
        ''' Sets the colormap that is displayed.
        map should be the string name of a colormap from matplotlib.cm'''
        self.cm = matplotlib.cm.get_cmap(map)
        self.Refresh()
        
    def SetLocalExtents(self, local_extents):
        #''' Sets the value axis min and max. Accepts a 2-tuple.'''
        self.local_extents = local_extents
        if self.local_extents[0] < self.global_extents[0]:
            self.global_extents[0] = self.local_extents[0]
        if self.local_extents[1] > self.global_extents[1]:
            self.global_extents[1] = self.local_extents[1]
        self.UpdateInterval()
        
    def SetGlobalExtents(self, global_extents):
        self.global_extents = global_extents
        self.UpdateInterval()
        
    def SetTicks(self, ticks):
        ''' Sets the number of tick marks displayed by the ColorBarPanel.
        1 or 0 will draw no ticks'''
        self.ticks = ticks
        self.Refresh()
    
    def UpdateLabelFormat(self):
        ''' Selects a number format based on the step value between ticks ''' 
        range = self.global_extents[1] - self.global_extents[0]
        step = range / self.ticks
        if 0 < step < 0.001:
            self.labelformat = '%.3e'
        else:
            self.labelformat = '%.3f'
        
    def OnToggleClipMode(self, evt):
        if self.clipmode == 'clip':
            self.clipmode = 'rescale'
        else:
            self.clipmode = 'clip'
        for win in self.notify_windows:
            win.SetClipInterval(self.GetLocalInterval(), self.local_extents, self.clipmode)
        self.Refresh()
        
    def OnRightDown(self, evt):
        popupMenu = wx.Menu()
        popupMenu.SetTitle('Colorbar')
        reset = popupMenu.AppendItem(wx.MenuItem(popupMenu, -1, 'Reset sliders'))
        self.Bind(wx.EVT_MENU, lambda(evt):self.ResetInterval(), reset)
        if self.clipmode == 'clip':
            bracket_mode = popupMenu.AppendItem(wx.MenuItem(popupMenu, -1, 'Value bracketing: RESCALE'))
        else:
            bracket_mode = popupMenu.AppendItem(wx.MenuItem(popupMenu, -1, 'Value bracketing: CLIP'))
        self.Bind(wx.EVT_MENU, self.OnToggleClipMode, bracket_mode)
        
        aggmethod = self.Parent.aggregationMethodsChoice.GetStringSelection().lower()
        src_table = self.Parent.sourceChoice.GetStringSelection()
        if (aggmethod in ['mean', 'median', 'min', 'max'] 
            and self.interval != self.global_extents 
            and src_table != p.object_table):
            popupMenu.AppendSeparator()
            saveitem = popupMenu.AppendItem(wx.MenuItem(popupMenu, -1, 'Save interval to properties as a filter'))
            self.Bind(wx.EVT_MENU, self.OnSaveIntervalAsFilter, saveitem)
        self.PopupMenu(popupMenu, (evt.X, evt.Y))
        
    def OnSaveIntervalAsFilter(self, evt):
        import DBConnect
        import os.path
        colname = self.Parent.measurementsChoice.GetStringSelection()
        
        lb = ub = ''
        if self.interval[0] != self.global_extents[0]:
            lb = ('%.3f<'%self.interval[0]).replace('.',',')
        if self.interval[1] != self.global_extents[1]:
            ub = ('<%.3f'%self.interval[1]).replace('.',',')
        filtername = 'filter_SQL_%s%s%s'%(lb, colname, ub)
        
        if lb and ub:
            where = '%s>%s AND %s<%s'%(colname, self.interval[0], colname, self.interval[1])
        elif lb:
            where = '%s>%s'%(colname, self.interval[0])
        elif ub: 
            where = '%s<%s'%(colname, self.interval[1])
            
        p.__dict__[filtername] = 'SELECT %s FROM %s WHERE %s'%(dbconnect.UniqueImageClause(), p.image_table, where)

        defaultPath, defaultFileName = os.path.split(p._filename)
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=defaultPath, defaultFile=defaultFileName,
                                   style=(wx.SAVE | wx.FD_OVERWRITE_PROMPT |wx.FD_CHANGE_DIR))
        if saveDialog.ShowModal()==wx.ID_OK:
            logging.info('Saving filter to %s'%(saveDialog.GetPath()))
            logging.debug('   '+filtername+' = '+p.__dict__[filtername])
            p.SaveFile(saveDialog.GetPath())
        saveDialog.Destroy()

        
    def OnResize(self, evt):
        range = self.global_extents[1] - self.global_extents[0]
        self.low_slider.SetPosition((self.Size[0] * (self.interval[0] - self.global_extents[0]) / range - s_off, -1))
        self.high_slider.SetPosition((self.Size[0] * (self.interval[1] - self.global_extents[0]) / range - s_off, -1))
        self.UpdateLabelFormat()
            
            
    def OnPaint(self, evt):
        w_global, h = self.Size
        if 0 in self.Size:
            return
        low_slider_pos  = self.low_slider.GetPositionTuple()[0] + s_off
        high_slider_pos = self.high_slider.GetPositionTuple()[0] + s_off
        
        global_scale = self.global_extents[1] - self.global_extents[0]  # value scale of the global data
        if global_scale == 0:
            local_x0 = 0
            local_x1 = w_global
            w_local = w_global
        else:
            local_x0 = (self.local_extents[0] - self.global_extents[0]) / global_scale * w_global     # x pos (pixels) to start drawing the local color bar
            local_x1 = (self.local_extents[1] - self.global_extents[0]) / global_scale * w_global     # x pos (pixels) to stop drawing the local color bar
            w_local = local_x1 - local_x0                                   # pixel width of the local color bar
        
        w0 = max(low_slider_pos, local_x0) - local_x0
        w1 = local_x1 - min(high_slider_pos, local_x1)
        
        # create array of values to be used for the color bar
        if self.clipmode=='rescale':
            a1 = np.zeros(w0)
            a2 = np.arange(abs(min(high_slider_pos, local_x1) - max(low_slider_pos, local_x0)), dtype=float) / (min(high_slider_pos, local_x1) - max(low_slider_pos, local_x0))
            a3 = np.ones(w1)
            a = np.hstack([a1,a2,a3])
        elif self.clipmode=='clip':
            a = np.arange(w_local, dtype=float) / w_local
            a[:w0] = 0.
            if w1>=1:
                a[-w1:] = 1.
        
        # draw the color bar
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        
        dc.SetPen(wx.Pen((0,0,0)))
        dc.DrawLine(0, (h-14)/2, local_x0, (h-14)/2)
        
        for x, v in enumerate(a):
            color = np.array(self.cm(v)) * 255
            dc.SetPen(wx.Pen(color))
            dc.DrawLine(x+local_x0, 0, x+local_x0, h-14)
        
        dc.SetPen(wx.Pen((0,0,0)))
        dc.DrawLine(local_x1, (h-14)/2, w_global, (h-14)/2)
        
        # draw value axis
        if self.ticks <= 1:
            return
        font = dc.GetFont()
        font.SetPixelSize((6,12))
        dc.SetFont(font)
        for t in xrange(self.ticks):
            xpos = t * w_global/(self.ticks-1.)
            val = t * (self.global_extents[1]-self.global_extents[0]) / (self.ticks-1)  + self.global_extents[0]
            dc.DrawLine(xpos,6,xpos,h-14)
            textpos = xpos - xpos/w_global * dc.GetFullTextExtent(self.labelformat%(val), font)[0]
            dc.DrawText(self.labelformat%(val), textpos, h-13)
            
        dc.EndDrawing()        
