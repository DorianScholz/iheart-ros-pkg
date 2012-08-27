#!/usr/bin/env python
import os, sys
from PyQt4 import QtGui, QtCore
from indicator_menu import IndicatorMenu

class QtIndicatorMenu(QtCore.QObject, IndicatorMenu):
    _update_menu_signal = QtCore.pyqtSignal(list)
        
    def __init__(self, indicator_name, icon_name, icon_path):
        super(QtIndicatorMenu, self).__init__()
        self._icon_path = icon_path
        self._icon_name = icon_name
        self._menu = None
        self._app = QtGui.QApplication(sys.argv)
        self._update_menu_signal.connect(self._update_menu)
        self._indicator = QtGui.QSystemTrayIcon(QtGui.QIcon(os.path.join(self._icon_path, self._icon_name)), self._app)
        self._menu = QtGui.QMenu()
        self._indicator.setContextMenu(self._menu)
        self._indicator.show()
        
    def _toolkit_create_separator(self):
        menu_item = QtGui.QAction(self)
        menu_item.setSeparator(True)
        return menu_item
        
    def _toolkit_create_menu_item(self, text, activate_callback=None):
        menu_item = QtGui.QAction(text, self)
        if activate_callback is not None:
            menu_item.triggered.connect(activate_callback)
        menu_item.set_sensitive = menu_item.setEnabled
        menu_item.set_submenu = menu_item.setMenu
        return menu_item
        
    def _toolkit_create_menu(self):
        menu = QtGui.QMenu()
        menu.append = lambda action: menu.addAction(action)
        return menu

    def set_icon(self, icon_name):
        self._indicator.setIcon(QtGui.QIcon(os.path.join(self._icon_path, icon_name)))

    def update_menu(self, menu_description):
        self._update_menu_signal.emit(menu_description)
        
    def _update_menu(self, menu_description):
        if self._menu is not None:
            self._menu.clear()
        for menu_item in self._create_menu_items(menu_description):
            self._menu.addAction(menu_item)

    def main(self):
        return self._app.exec_()
