import panasonic_viera
from django.http import HttpResponse
from django.shortcuts import redirect
from concurrent.futures import ThreadPoolExecutor

import os
import time
import panasonic_viera

import threading


class TestVierraThread():
    def __init__(self):
        self.radio = None
        self.mode = None
        self.rc = None
        self.display_status = None
        self.tv_status = None
        self.lock = threading.Lock()
        try:
            self.rc = panasonic_viera.RemoteControl("10.18.20.142", app_id="AVp+pgBQVrNCxQ==",
                                                    encryption_key="aEej7rMTeh5y1hvVz1DkgQ==")
        except Exception:
            raise Exception('TV OFFFLINE')
        self.get_tv_status()

    def tv_power(self):
        self.tv_status = False
        self.rc.turn_off()

    def get_tv_status(self):
        with self.lock:
            try:
                self.rc.get_mute()
                self.tv_status = True
            except Exception as e:
                self.tv_status = False
                self.rc._session_seq_num += 1
            return self.tv_status

    def get_display_status(self):
        with self.lock:
            return self.display_status

    def debug(self):
        print(f'Radio:{self.radio}\nDisplay:{self.display_status}\nMode:{self.mode}\nTV_Stauts{self.tv_status}')

    def turn_display_off(self):

        t = 0.85
        self.rc.send_key(panasonic_viera.Keys.menu)
        time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.enter)
        time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.right)
        time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.enter)
        time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.enter)
        time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.down)
        time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.enter)
        self.display_status = False

    def turn_display_on(self):
        self.rc.send_key(panasonic_viera.Keys.enter)
        self.display_status = True

    def radio_and_info(self):
        if self.tv_status:
            os.system('sh /home/tcl/1live.sh')
            self.radio = True
        else:
            self.tv_power()
            self.tv_status = True
            os.system('sh /home/tcl/1live.sh')
            self.radio = True
        if not self.display_status:
            self.turn_display_on()

    def only_radio(self):
        # Radio Only
        self.radio = True
        if self.tv_status:
            self.turn_display_off()
        else:
            self.tv_power()
            self.tv_status = True
            time.sleep(3)
            self.turn_display_off()
        os.system('sh /home/tcl/1live.sh')

    def only_info(self):
        print('innradio', self.radio)
        if self.radio:
            os.system('pkill vlc')
            self.radio = False
        if not self.display_status:
            self.turn_display_on()
        if not self.tv_status:
            self.tv_power()


import threading
import datetime
import time



