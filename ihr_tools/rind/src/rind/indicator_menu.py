#!/usr/bin/env python

class IndicatorMenu(object):
    
    def _create_menu_item(self, text=None, enabled=True, activate=None, indentation='', **kwargs):
        if text is None:
            menu_item = self._toolkit_create_separator()
        else:
            menu_item = self._toolkit_create_menu_item(indentation + text, activate)
            menu_item.set_sensitive(enabled)
        menu_item.user_args = kwargs
        return menu_item
    
    def _create_menu_items(self, menu_description, indentation=''):
        menu_items = []
        for menu_item_description in menu_description:
            menu_item = self._create_menu_item(indentation=indentation, **menu_item_description)
            menu_items.append(menu_item)
            if menu_item_description.get('submenu_description', None) is not None:
                menu_item.set_submenu(self._create_menu(menu_item_description['submenu_description']))
            if menu_item_description.get('subitem_description', None) is not None:
                for sub_item in self._create_menu_items(menu_item_description['subitem_description'], indentation=indentation + '  '):
                    menu_items.append(sub_item)
        return menu_items
    
    def _create_menu(self, menu_description):
        menu = self._toolkit_create_menu()
        for menu_item in self._create_menu_items(menu_description):
            menu.append(menu_item)
        return menu
