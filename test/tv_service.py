import os, time, select, errno
import panasonic_viera
import threading
import socket
import select
import sqlite3

import logging

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
logging.getLogger("panasonic_viera").setLevel(logging.ERROR)


def get_db_state(column='state'):
    with sqlite3.connect(r'/home/tcl/InfoDisplay/db.sqlite3') as conn:
        cur = conn.cursor()
        cur.execute(f'SELECT {column} FROM InfoDisplay_TV_State WHERE ID = 1')
        return int(cur.fetchone()[0])


def update_db(field: str, value: str):
    with sqlite3.connect(r'/home/tcl/InfoDisplay/db.sqlite3') as conn:
        cur = conn.cursor()
        cur.execute(f'UPDATE InfoDisplay_TV_State SET {field} = {value} WHERE ID = 1')


class TV_Service:
    def __init__(self):
        self.rc = None
        self.error = None

    def check_online_status(self):
        try:
            self.rc.get_mute()
            self.error = None
        except Exception:
            self.error = 'TV Offline'

    def connect(self):
        try:
            self.rc = panasonic_viera.RemoteControl("10.18.20.142", app_id="AVp+pgBQVrNCxQ==",
                                                    encryption_key="aEej7rMTeh5y1hvVz1DkgQ==")
            self.error = None
            return True
        except Exception:
            self.error = 'TV Offline'


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
        time.sleep(t)
        update_db('r_dis_state', False)

    def restore_settings(self):
        time.sleep(20)
        self.rc = panasonic_viera.RemoteControl("10.18.20.142", app_id="AVp+pgBQVrNCxQ==",
                                                encryption_key="aEej7rMTeh5y1hvVz1DkgQ==")

        print('restoring settings')
        t = 1

        self.rc.send_key(panasonic_viera.Keys.menu)
        time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.enter)
        time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.right)
        time.sleep(t)
        for i in range(19):
            self.rc.send_key(panasonic_viera.Keys.down)
            time.sleep(t)
        self.rc.send_key(panasonic_viera.Keys.enter)
        time.sleep(t)
        for i in range(3):
            self.rc.send_key(panasonic_viera.Keys.down)
            time.sleep(t)

        self.rc.send_key(panasonic_viera.Keys.exit)
        time.sleep(1.2)

        self.display_status = True
        update_db('r_dis_state', True)

    def turn_display_on(self):
        self.rc.send_key(panasonic_viera.Keys.enter)
        update_db('r_dis_state', True)


class SocketThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.counter = None
        self.running = False
        self.tv_thread = TV_Service()

        self.current_mode = get_db_state()

    def eval_current_mode(self):
        display_status = bool(get_db_state('r_dis_state'))
        logging.info(f'Current mode: {self.current_mode}')
        logging.debug(f'DP_Status v: {display_status}')
        if self.current_mode == 1:
            os.system('pkill vlc')
            os.system('sh /home/tcl/1live.sh')
            if not display_status:
                self.tv_thread.turn_display_on()

        elif self.current_mode == 2:
            os.system('pkill vlc')
            os.system('sh /home/tcl/1live.sh')
            if display_status:
                self.tv_thread.turn_display_off()
        elif self.current_mode == 3:
            os.system('pkill vlc')
            # if not self.tv_thread.display_status:
            if not display_status:
                self.tv_thread.turn_display_on()

        elif self.current_mode == 4:
            os.system('pkill vlc')
            if display_status:
                self.tv_thread.turn_display_off()


        #update_db('tv_dis_state', str(self.tv_thread.display_status))
        logging.debug(f"DP_Status  a: {bool(get_db_state('r_dis_state'))}")


    def run(self):
        self.running = True
        self.counter = 0

        if self.tv_thread.connect():
            logging.info('TV Verbunden und Eingeschaltet')
            self.eval_current_mode()

        while self.running:
            # self.counter += 1
            time.sleep(0.5)

            self.tv_thread.check_online_status()

            if not self.tv_thread.error:
                if get_db_state() != self.current_mode:
                    self.current_mode = get_db_state()
                    logging.debug(f'Mode Changed: {self.current_mode}')
                    self.eval_current_mode()

            elif self.tv_thread.error:
                logging.info('Reconnecting ...')
                while self.tv_thread.error:
                    self.tv_thread.connect()
                    if self.tv_thread.error is None:
                        logging.info('Success reconnect !')
                        time.sleep(1)
                        self.tv_thread.restore_settings()
                        self.counter = 0
                        self.eval_current_mode()


if __name__ == '__main__':
    test = SocketThread()
    test.start()
