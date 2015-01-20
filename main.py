#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from logger import Logger
from nls import _
from constant import PROGRAM_VERSION, PROGRAM_NAME_LONG
from player import Player


class DeepinMusicApp(Logger):
    app_instance = None
    app_ready = False
    db_ready = False
    splash = None

    def __init__(self):

        (self.options, self.args) = self.get_options().parse_args()

        # Run preload.
        self.run_preload()

        # initial mainloop setup. The actual loop is started later,
        self.mainloop_init()

        import helper
        helper.NEED_RESTORE = False if self.args else True

        # load the rest.
        self.__init()

    def run_preload(self):
        if self.options.Debug is not None:
            import logger
            try:
                logger.setLevelNo(int(self.options.Debug))
            except:
                print "Debug level incorrect"
                sys.exit(0)

        if self.options.MimetypeSupport:
            from common import FORMATS
            print "Mimetypes supported: ",
            print ",".join([",".join(i._mimes) for i in FORMATS])
            print "Missing Gstreamer plugins for full support: N/A "
            sys.exit(0)

        if self.options.ShowVersion:
            self.version()
            sys.exit(0)

    def get_options(self):

        from optparse import OptionParser, OptionGroup, IndentedHelpFormatter

        class OverrideHelpFormatter(IndentedHelpFormatter):

            """
                Merely for translation purposes
            """

            def format_usage(self, usage):
                return '%s\n' % usage

        usage = _("Usage: deepin-music-player [OPTION]... [URI]")
        optionlabel = _('Options')  # Merely for translation purposes
        p = OptionParser(usage=usage, add_help_option=False,
                         formatter=OverrideHelpFormatter())

        group = OptionGroup(p, _('Control Options'))
        group.add_option("-n", "--next", dest="Next",
                         action="store_true", default=False, help=_("Play the next track"))
        group.add_option("-p", "--prev", dest="Prev",
                         action="store_true", default=False, help=_("Play the previous track"))
        group.add_option("-t", "--play-pause", dest="PlayPause",
                         action="store_true", default=False, help=_("Pause or resume playback"))
        group.add_option("-f", "--forward", dest="Forward",
                         action="store_true", default=False, help=_("Seek Forward"))
        group.add_option("-r", "--rewind", dest="Rewind",
                         action="store_true", default=False, help=_("Seek Backward"))
        group.add_option("-s", "--stop", dest="Stop",
                         action="store_true", default=False, help=_("Stop playback"))

        p.add_option_group(group)

        group = OptionGroup(p, _('Volume Options'))
        group.add_option("-v", "--change-vol", dest="ChangeVolume",
                         action="store", default=None, help=_("Change Volume (VOLUME 0.0-1.0)"))
        p.add_option_group(group)

        group = OptionGroup(p, _('Track information Options'))
        group.add_option("--get-title", dest="GetTitle",
                         action="store_true", default=False, help=_("Print the title of current track"))
        group.add_option("--get-album", dest="GetAlbum",
                         action="store_true", default=False, help=_("Print the album of current track"))
        group.add_option("--get-artist", dest="GetArtist",
                         action="store_true", default=False, help=_("Print the artist of current track"))
        group.add_option("--get-length", dest="GetLength",
                         action="store_true", default=False, help=_("Print the length of current track"))
        group.add_option("--get-path", dest="GetPath",
                         action="store_true", default=False, help=_("Print the path of current track"))
        group.add_option("--current-position", dest="CurrentPosition",
                         action="store_true", default=False, help=_("Print current playback position"))
        p.add_option_group(group)

        group = OptionGroup(p, _('Other Options'))
        group.add_option("-h", "--help", action="help",
                         help=_("Show this help message and exit"))
        group.add_option("--new", dest="NewInstance", action="store_true",
                         default=False, help=_("Start new instance"))
        group.add_option("--version", dest="ShowVersion", action="store_true",
                         help=_("Show program's version number and exit."))
        group.add_option("--start-minimized", dest="StartMinimized",
                         action="store_true", default=False, help=_("Minimize after started"))
        group.add_option("--toggle-visible", dest="GuiToggleVisible",
                         action="store_true", default=False,
                         help=_("Toggle visibility of the GUI (if possible)"))
        group.add_option("--start-anyway", dest="StartAnyway",
                         action="store_true", default=False,
                         help=_("This option makes control options, such as --play to start program"))
        p.add_option_group(group)

        group = OptionGroup(p, _('Development/Debug Options'))
        group.add_option("--debug", dest="Debug", action="store",
                         default=None, help=_("Set debug level (0-9)"))
        # group.add_option('--startgui', dest='StartGui', action='store_true', default=False)
        # group.add_option('--no-dbus', dest='Dbus', action='store_false', default=True, help="Disable D-Bus support")
        group.add_option("--mimetype-support", action="store_true", dest="MimetypeSupport", default=False,
                         help=_("Show information supported audio file"))
        p.add_option_group(group)

        return p

    def version(self):
        print "%s %s" % (PROGRAM_NAME_LONG, PROGRAM_VERSION)

    def mainloop_init(self):
        import gobject
        gobject.threads_init()

        # dbus_init.
        import dbus
        import dbus.mainloop.glib
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.gthreads_init()

    def __init(self):
        # Loading configure.
        self.loginfo("Loading settings...")
        from config import config
        config.load()

        # Loading MediaDB.
        self.loginfo("Loading MediaDB...")
        from library import MediaDB
        MediaDB.connect("loaded", self.on_db_loaded)
        MediaDB.load()

        # Loading Chinese to Pinyin DB.
        from pinyin import TransforDB
        TransforDB.load()

        import utils
        import os
        utils.saveJsonDB(
            TransforDB.dict_objs, os.path.join(os.getcwd(), 'data', 'pinyin.json'))

        # initialize Gui
        self.loginfo("Initialize over")

    def on_ready_cb(self, app):
        print("++++++++++++++++++++++")
        self.app_ready = True
        import glib
        if self.splash is not None:
            glib.idle_add(self.splash.destroy)
        self.post_start()

    def on_db_loaded(self, *args, **kwargs):
        self.db_ready = True
        self.post_start()

    def post_start(self):
        if self.db_ready and self.app_ready:
            # restore = True
            if self.app_instance:
                current_view = self.app_instance.playlist_ui.get_selected_song_view()
                from utils import convert_args_to_uris
                args = convert_args_to_uris(self.args)
                if len(args) > 0:
                    if current_view:
                        # restore = False
                        current_view.add_file(args[0], play=True)
                if args[1:]:
                    if current_view:
                        current_view.async_add_uris(args[1:], False)
            # if restore:
            #     from player import Player
            #     Player.load()

            if self.options.StartAnyway and self.check_result == "command":
                import dbus_manager
                dbus_manager.run_commands(self.options, self.dbus)

            self.start_fetch_manager()

    def start_fetch_manager(self):
        SimpleFetchManager()

    def __show_splash(self):
        import widget
        from config import config
        self.splash = widget.show_splash(False)

if __name__ == "__main__":

    app = QApplication(sys.argv)
    from gui.lrcwidget import MainWindow
    main = MainWindow()
    main.show()
    musicPlayer = DeepinMusicApp()

    from library import MediaDB
    song = MediaDB.get_random_song()
    Player.play_new(song, seek=song.get("seek", None))

    exitCode = app.exec_()
    sys.exit(exitCode)
