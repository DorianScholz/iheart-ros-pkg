#!/usr/bin/env python
import gtk
import appindicator
from indicator_menu import IndicatorMenu

class GtkIndicatorMenu(IndicatorMenu):
        
    def __init__(self, indicator_name, icon_name, icon_path):
        self._indicator = appindicator.Indicator(indicator_name, icon_name.rsplit('.', 1)[0], appindicator.CATEGORY_APPLICATION_STATUS, icon_path)
        self._indicator.set_status(appindicator.STATUS_ACTIVE)
        
    def _toolkit_create_separator(self):
        menu_item = gtk.SeparatorMenuItem()
        menu_item.show()
        return menu_item
        
    def _toolkit_create_menu_item(self, text, activate_callback=None):
        menu_item = gtk.MenuItem(text.replace('_', '__'))
        if activate_callback is not None:
            menu_item.connect('activate', activate_callback)
        menu_item.show()
        return menu_item
        
    def _toolkit_create_menu(self):
        menu = gtk.Menu()
        menu.set_double_buffered(True)
        return menu
    
    def set_icon(self, icon_name):
        self._indicator.set_icon(icon_name.rsplit('.', 1)[0])

    def update_menu(self, menu_description):
        gtk.gdk.threads_enter()
        self._indicator.set_menu(self._create_menu(menu_description))
        gtk.gdk.threads_leave()

    def main(self):
        gtk.gdk.threads_init()
        return gtk.main()
