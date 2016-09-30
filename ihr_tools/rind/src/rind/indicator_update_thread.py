#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2008, I Heart Engineering
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of I Heart Engineering nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import time
import os
import signal
import subprocess
from threading import Thread
import sys
import glob
from exceptions import IOError

import roslib; roslib.load_manifest('rind')
import rosgraph.masterapi
import rosnode

class IndicatorUpdateThread(Thread):
    _default_config = {
        'launchers': [
            {'text': 'rqt_gui', 'rosdep': 'rqt_gui', 'command': 'rosrun rqt_gui rqt_gui'},
            {'text': 'rxConsole', 'rosdep': 'rxtools', 'command': 'rxconsole'},
        ],
        'menu_parts': ['roscore', 'topics', 'services', 'nodes', 'launchers', 'quit'],
    }
    def __init__(self, indicator):
        super(IndicatorUpdateThread, self).__init__()
        self._indicator = indicator
        self._exit = False
        self._master = rosgraph.masterapi.Master('/rind')
        self._master_online = 0
        self._roscore_pid = None
        self._topics = [] # List of Topics
        self._nodes = [] # List of Topics
        self._publishers = {} # Publishers keyed by topic
        self._subscribers = {} # Subscribers keyed by topic
        self._menu_description = []
        self._launchers = []
        self.load_config(os.path.join(os.environ['HOME'], '.ros', 'rind.conf'))

    def load_config(self, config_file_name):
        config_file = None
        try:
            config_file = open(config_file_name)
        except IOError, e:
            print 'Could not read configuration from file at:%s\n%s' % (config_file_name, e)

        config_from_file = {}
        if config_file is not None:
            try:
                config_from_file = eval(config_file.read())
            except Exception, e:
                print 'Could not parse configuration: %s' % e

        self._config = self._default_config.copy()
        self._config.update(config_from_file)

        for launcher in self._config['launchers']:
            if 'rosdep' not in launcher or roslib.packages.get_pkg_dir(launcher['rosdep'], required=False) is not None:
                launcher['activate'] = self._on_menu_item_launch
                self._launchers.append(launcher)

    def check_master(self):
        if not self._master_online and self._master.is_online():
            print 'Master has come online'
            self._master_online = True
            self._indicator.set_icon('rind-panel.svg')

            try:
                # try to get roscore's pid from the pid of rosmaster
                self._roscore_pid = int(subprocess.check_output(['ps', '-p', '%d' % self._master.getPid(), '-oppid=']).strip())
            except:
                # try to get roscore's pid from .pid file
                pid_files = glob.glob(os.path.join(os.environ['HOME'], '.ros', 'roscore*.pid'))
                if pid_files and os.access(pid_files[0], os.R_OK):
                    pid_file = open(pid_files[0], 'r')
                    self._roscore_pid = int(pid_file.readline())
                else:
                    self._roscore_pid = None

            print 'ROS Core pid', self._roscore_pid

        elif self._master_online and not self._master.is_online():
            print 'Master has gone offline'
            self._master_online = False
            self._indicator.set_icon('rind-idle.svg')
            self._topics = []
            self._nodes = []
            self._roscore_pid = None
            self._publishers = {}
            self._subscribers = {}

    def update_topic_info(self):
        if self._master.is_online():
            topic_pubs, topic_subs, service_providers = self._master.getSystemState()
            self._publishers = dict(topic_pubs)
            self._subscribers = dict(topic_subs)
            self._service_providers = dict(service_providers)
            self._topics = sorted(set(self._publishers.keys() + self._subscribers.keys()))
        else:
            self._topics = []
            self._publishers = {}
            self._subscribers = {}
            self._service_providers = {}

    def update_node_info(self):
        self._nodes = []
        if self._master.is_online():
            self._nodes = rosnode.get_node_names()

    def _on_menu_item_quit(self, menu_item):
        print 'Shutting down'
        self.stop()
        # Shutdown here...
        sys.exit(0)

    def _on_menu_item_launch(self, menu_item):
        if 'command' in menu_item.user_args:
            subprocess.Popen(menu_item.user_args['command'], shell=True, stdin=None, stdout=None, stderr=None, cwd=os.environ['HOME'])
        else:
            print 'No command found in user_args:', menu_item.user_args

    def _on_menu_item_roscore(self, menu_item):
        if self._master_online:
            if self._roscore_pid is not None:
                print 'Stopping ROS Core'
                os.kill(self._roscore_pid, signal.SIGINT)
            else:
                print 'Error Stopping ROS Core by PID'
        else:
            print 'Starting ROS Core'
            #subprocess.Popen(['roscore'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.environ['HOME'])
            subprocess.Popen(['roscore > /dev/null'], shell=True, stdin=None, stdout=None, stderr=None, cwd=os.environ['HOME'])

    def _menu_add_submenu(self, menu_description, submenu_name, submenu_description, folding_item_count=5, seperator=False):
        if len(submenu_description) == 0:
            return
        if seperator:
            menu_description.append({})
        menu_description.append({'text': submenu_name})
        if len(submenu_description) > folding_item_count:
            menu_description[-1]['submenu_description'] = submenu_description
        else:
            menu_description[-1]['subitem_description'] = submenu_description
            menu_description[-1]['enabled'] = False

    def _menu_add_roscore(self, menu_description):
        menu_item_description = {'activate': self._on_menu_item_roscore}
        if self._master_online:
            if self._roscore_pid is not None:
                menu_item_description['text'] = 'Shutdown ROS Core'
            else:
                menu_item_description['text'] = 'Connected to ROS Master'
                menu_item_description['enabled'] = False
        else:
            menu_item_description['text'] = 'Launch ROS Core'
        menu_description.append(menu_item_description)

    def _menu_add_topics(self, menu_description):
        if len(self._topics) > 0:
            topic_menu_descripion = []
            for topic in self._topics:
                submenu_description = []

                publisher_menu_description = []
                for publisher in self._publishers.get(topic, []):
                    publisher_menu_description.append({'text': publisher, 'enabled': False})
                self._menu_add_submenu(submenu_description, 'Publishers', publisher_menu_description)

                subscriber_menu_description = []
                for subscriber in self._subscribers.get(topic, []):
                    subscriber_menu_description.append({'text': subscriber, 'enabled': False})
                self._menu_add_submenu(submenu_description, 'Subscribers', subscriber_menu_description)

                self._menu_add_submenu(topic_menu_descripion, topic, submenu_description, folding_item_count=0)

            self._menu_add_submenu(menu_description, 'Topics', topic_menu_descripion, seperator=True)

    def _menu_add_services(self, menu_description):
        if len(self._service_providers) > 0:
            service_menu_descripion = []
            for service in sorted(self._service_providers.keys()):
                submenu_description = []

                provider_description = []
                for provider in self._service_providers.get(service, []):
                    provider_description.append({'text': provider, 'enabled': False})
                self._menu_add_submenu(submenu_description, 'Providers', provider_description)

                self._menu_add_submenu(service_menu_descripion, service, submenu_description, folding_item_count=0)

            self._menu_add_submenu(menu_description, 'Services', service_menu_descripion, seperator=True)

    def _menu_add_nodes(self, menu_description):
        self.update_node_info()
        if len(self._nodes) > 0:
            node_menu_description = []
            for node in self._nodes:
                node_menu_description.append({'text': node, 'enabled': False})

            self._menu_add_submenu(menu_description, 'Nodes', node_menu_description, seperator=True)

    def _menu_add_launchers(self, menu_description):
        if self._master_online:
            self._menu_add_submenu(menu_description, 'Launchers', self._launchers, seperator=True)

    def _menu_add_quit(self, menu_description):
        menu_description.append({})
        menu_description.append({'text': 'Quit', 'activate': self._on_menu_item_quit})

    def build_menu_description(self):
        menu_description = []
        for menu_part in self._config['menu_parts']:
            getattr(self, '_menu_add_%s' % menu_part)(menu_description)
        return menu_description

    def run(self):
        while not self._exit:
            self.check_master()
            if 'topics' in self._config['menu_parts'] or 'services' in self._config['menu_parts']:
                self.update_topic_info()
            menu_descripion = self.build_menu_description()
            if str(self._menu_description) != str(menu_descripion):
                self._menu_description = menu_descripion
                self._indicator.update_menu(menu_descripion)
            time.sleep(1)

    def stop(self):
        self._exit = True
