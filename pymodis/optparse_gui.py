# -*- coding: utf-8 -*-

'''
A drop-in replacement for optparse ("import optparse_gui as optparse")
Provides an identical interface to optparse(.OptionParser),
But displays an automatically generated wx dialog in order to enter the
options/args, instead of parsing command line arguments
'''

import os
import sys
import re
import optparse

import wx

__version__ = 0.2
__revision__ = '$Id$'

#for required options
strREQUIRED = 'required'


class OptparseDialog(wx.Dialog):
    '''The dialog presented to the user with dynamically generated controls,
    to fill in the required options.
    Based on the wx.Dialog sample from wx Docs & Demos'''
    def __init__(
            self,
            optParser,  # The OptionParser object
            title,
            name,
            parent=None,
            ID=0,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE,
            ):

        provider = wx.SimpleHelpProvider()
        wx.HelpProvider_Set(provider)

        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, ID, title, pos, size, style)

        self.PostCreate(pre)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.option_controls = {}

#       IN THE TOP OF GUI THERE WAS THE NAME OF THE SCRIPT, BUT NOW IT IS IN
#       THE TITLE

#        top_label_text = '%s %s' % (optParser.get_prog_name(),
#                                     optParser.get_version())
#        label = wx.StaticText(self, -1, top_label_text)
#        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        # Add a text control for entering args

        arg = self._checkArg(optParser.get_prog_name())
        sizer.Add(arg, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT |
                  wx.TOP, 5)

        self.browse_option_map = {}

        # Add controls for all the options
        for option in optParser.option_list:
            if option.dest is None:
                continue

            if option.help is None:
                option.help = u''

            box = wx.BoxSizer(wx.HORIZONTAL)
            if 'store' == option.action:
                label = wx.StaticText(self, -1, option.dest)
                label.SetHelpText(option.help)
                box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

                if 'choice' == option.type:
                    if optparse.NO_DEFAULT == option.default:
                        option.default = option.choices[0]
                    ctrl = wx.ComboBox(
                        self, -1, choices=option.choices,
                        value=option.default,
                        style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT
                    )
                else:
                    if 'MULTILINE' in option.help:
                        ctrl = wx.TextCtrl(self, -1, "", size=(300, 100),
                                           style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
                    else:
                        ctrl = wx.TextCtrl(self, -1, "", size=(300, -1))

                    if (option.default != optparse.NO_DEFAULT) and \
                       (option.default is not None):
                        ctrl.Value = unicode(option.default)

                box.Add(ctrl, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

                if option.type in ['file', 'directory']:
                    browse = wx.Button(self, label='...')
                    browse.SetHelpText('Click to open %s browser' % (option.type))
                    self.browse_option_map[browse.GetId()] = option, ctrl
                    wx.EVT_BUTTON(self, browse.GetId(), self.OnSelectPath)
                    box.Add(browse, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

            elif option.action in ('store_true', 'store_false'):
                ctrl = wx.CheckBox(self, -1, option.dest, size=(300, -1))
                box.Add(ctrl, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
            else:
                raise NotImplementedError('Unknown option action: %s' % repr(option.action))

            ctrl.SetHelpText(option.help)
            sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

            self.option_controls[option] = ctrl

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("The OK button completes the dialog")
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def OnSelectPath(self, event):
        option, ctrl = self.browse_option_map[event.GetId()]
        path = os.path.abspath(ctrl.Value)
        if option.type == 'file':
            dlg = wx.FileDialog(self,
                                message='Select file for %s' % (option.dest),
                                defaultDir=os.path.dirname(path),
                                defaultFile=path)
        elif option.type == 'directory':
            if os.path.isfile(path):
                path = os.path.dirname(path)
            dlg = wx.DirDialog(self,
                               message='Select directory for %s' % (option.dest),
                               defaultPath=path)
        else:
            raise NotImplementedError(repr(option.type))
        dlg_result = dlg.ShowModal()
        if wx.ID_OK != dlg_result:
            return
        ctrl.Value = dlg.GetPath()
##        import open_py_shell;open_py_shell.open_py_shell(locals())

    def _getOptions(self):
        option_values = {}
        for option, ctrl in self.option_controls.iteritems():
            option_values[option] = ctrl.Value

        return option_values

    def _getArgs(self):
        args_buff = self.args_ctrl.Value
        args = re.findall(r'(?:((?:(?:\w|\d)+)|".*?"))\s*', args_buff)
        return args

    def _checkArg(self, name):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if name == 'modis_convert.py' or name == 'modis_parse.py':
            ltext = 'File HDF'
            self.htext = 'Select HDF file'
        elif name == 'modis_download.py':
            ltext = 'Destination Folder'
            self.htext = 'Select directory where save MODIS files'
        elif name == 'modis_mosaic.py':
            ltext = 'File containig HDF list'
            self.htext = 'Select file containig a list of MODIS file'
        elif name == 'modis_multiparse.py':
            ltext = 'List of HDF file'
            self.htext = 'List of MODIS files'
        label = wx.StaticText(self, -1, ltext)
        label.SetHelpText(self.htext)
        self.args_ctrl = wx.TextCtrl(parent=self, id=wx.ID_ANY, value='',
                                     size=(100, -1), style=0)
        bbrowse = wx.Button(parent=self, id=wx.ID_ANY, label='Browse',
                            size=(-1, -1))
        sizer.Add(item=label, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTRE_VERTICAL |
                  wx.ALL, border=5)
        sizer.Add(item=self.args_ctrl, flag=wx.ALIGN_LEFT |
                  wx.ALIGN_CENTRE_VERTICAL | wx.ALL, border=5)
        sizer.Add(item=bbrowse, flag=wx.ALIGN_LEFT | wx.ALL, border=5)
        bbrowse.Bind(wx.EVT_BUTTON, self.OnBrowse)
        self.args_ctrl.Bind(wx.EVT_TEXT, self.OnText)
        return sizer

    def OnText(self, event):
        """!File changed"""
        self.wktfile = event.GetString()
        if len(self.wktfile) > 0 and os.path.isfile(self.wktfile):
            print 'ok'
            #TODO
        event.Skip()

    def OnBrowse(self, event):
        """!Choose file"""
        dlg = wx.FileDialog(parent=self, message=self.htext,
                            defaultDir=os.getcwd(), style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.args_ctrl.SetValue(path)
        dlg.Destroy()
        event.Skip()

    def getOptionsAndArgs(self):
        '''Returns the tuple (options, args)
        options -  a dictionary of option names and values
        args - a sequence of args'''

        option_values = self._getOptions()
        args = self._getArgs()
        return option_values, args


class UserCancelledError(Exception):
    pass


class Option(optparse.Option):
    SUPER = optparse.Option
    TYPES = SUPER.TYPES + ('file', 'directory')

    #for required options
    ATTRS = optparse.Option.ATTRS + [strREQUIRED]

    def __init__(self, *opts, **attrs):
        if attrs.get(strREQUIRED, False):
            attrs['help'] = '(Required) ' + attrs.get('help', "")
        optparse.Option.__init__(self, *opts, **attrs)


class OptionParser(optparse.OptionParser):
    SUPER = optparse.OptionParser

    def __init__(self, *args, **kwargs):
        if wx.GetApp() is None:
            self.app = wx.App(False)

        if 'option_class' not in kwargs:
            kwargs['option_class'] = Option
        self.SUPER.__init__(self, *args, **kwargs)

    def parse_args(self, args=None, values=None):
        '''
        This is the heart of it all - overrides optparse.OptionParser.parse_args
        @param arg is irrelevant and thus ignored,
               it's here only for interface compatibility
        '''
        # preprocess command line arguments and set to defaults
        option_values, args = self.SUPER.parse_args(self, args, values)
        for option in self.option_list:
            if option.dest and hasattr(option_values, option.dest):
                default = getattr(option_values, option.dest)
                if default is not None:
                    option.default = default

        dlg = OptparseDialog(optParser=self, name=self.description,
                             title="%s GUI" % self.description)

        if args:
            dlg.args_ctrl.Value = ' '.join(args)

        dlg_result = dlg.ShowModal()
        if wx.ID_OK != dlg_result:
            raise UserCancelledError('User has canceled')

        if values is None:
            values = self.get_default_values()

        option_values, args = dlg.getOptionsAndArgs()

        for option, value in option_values.iteritems():
            if ('store_true' == option.action) and (value is False):
                setattr(values, option.dest, False)
                continue
            if ('store_false' == option.action) and (value is True):
                setattr(values, option.dest, False)
                continue

            if option.takes_value() is False:
                value = None

            option.process(option, value, values, self)

        return values, args

    def error(self, msg):
        wx.MessageDialog(None, msg, 'Error!', wx.ICON_ERROR).ShowModal()
        return self.SUPER.error(self, msg)


#############################################################################

def sample_parse_args():
    usage = "usage: %prog [options] args"
    if 1 == len(sys.argv):
        optParser_class = OptionParser
    else:
        optParser_class = optparse.OptionParser

    parser = optParser_class(usage=usage, version='0.1')
    parser.add_option("-f", "--file", dest="filename", default=r'c:\1.txt',
                      help="read data from FILENAME")
    parser.add_option("-t", "--text", dest="text", default=r'c:\1.txt',
                      help="MULTILINE text field")
    parser.add_option("-a", "--action", dest="action",
                      choices=['delete', 'copy', 'move'],
                      help="Which action do you wish to take?!")
    parser.add_option("-n", "--number", dest="number", default=23,
                      type='int',
                      help="Just a number")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose",
                      help='To be or not to be? (verbose)')

    (options, args) = parser.parse_args()
    return options, args


def sample_parse_args_issue1():
    usage = "usage: %prog [options] args"
    optParser_class = OptionParser

    parser = optParser_class(usage=usage, version='0.1')
    parser.add_option("-f", "--file", dest="filename", default=r'c:\1.txt',
                      type='file',
                      help="read data from FILENAME")
    parser.add_option("-t", "--text", dest="text", default=r'c:\1.txt',
                      help="MULTILINE text field")
    parser.add_option("-a", "--action", dest="action",
                      choices=['delete', 'copy', 'move'],
                      help="Which action do you wish to take?!")
    parser.add_option("-n", "--number", dest="number", default=23,
                      type='int',
                      help="Just a number")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose",
                      help='To be or not to be? (verbose)')

    (options, args) = parser.parse_args()
    return options, args


def main():
    options, args = sample_parse_args_issue1()
    print 'args: %s' % repr(args)
    print 'options: %s' % repr(options)

if '__main__' == __name__:
    main()