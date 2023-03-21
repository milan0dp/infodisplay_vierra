import datetime
import os
from pathlib import Path
import PIL.Image
import panasonic_viera
from django.http import HttpResponse
from django.shortcuts import render, redirect
import fitz
from .forms import ResumeUpload
from .models import *
from concurrent.futures import ThreadPoolExecutor
import time, threading
import pytz, socket

Refresh_req = False

crt = False


# def com_thread(data):
#     global crt, client_socket
#
#     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     client_socket.connect(('localhost', 64321))
#
#     client_socket.sendall(data.encode())
#     response = client_socket.recv(1024).decode()
#
#     return response





# def set_mode(mode):
#     if mode == 1:
#         # radio and info
#         os.system('sh /home/tcl/1live.sh')
#         com_thread('dis_on')
#     elif mode == 2:
#         # only radio
#         com_thread('dis_off')
#         os.system('sh /home/tcl/1live.sh')
#     elif mode == 3:
#         os.system('pkill vlc')
#         com_thread('dis_on')


class TimeCheckerThread(threading.Thread):
    def __init__(self, start_time, end_time):
        threading.Thread.__init__(self)
        self.start_time = start_time
        self.end_time = end_time
        self.stopped = False

    def run(self):
        while not self.stopped:

            tz = pytz.timezone('Europe/Berlin')
            current_time = datetime.datetime.now(tz).time()

            print(current_time, self.start_time, self.end_time)
            ob = TV_State.objects.get(id=1)
            ob.last_state = ob.state
            ob.save()
            ob = TV_State.objects.get(id=1)
            if current_time < self.start_time or current_time > self.end_time:
                ob.state = 4
            else:
                ob.state = ob.last_state

            ob.save()
            time.sleep(10)  # Check every minute

    def update_times(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time


def update_live_folder(file):
    if file[-4:] == '.pdf':

        doc = fitz.Document(os.path.join(Path(__file__).resolve().parent.parent.parent, 'data', file))

        for p in doc:
            print("Converting | Page ", p)
            pix = p.get_pixmap(dpi=400)
            pix.save(
                os.path.join(Path(__file__).resolve().parent.parent.parent, 'data', file[:-3] + str(p.number) + '.jpg'))


def file_order_update(request, file, order):
    if not upload_file.objects.filter(data='data/' + file).exists():
        return redirect('/up')
    else:
        file_instance = upload_file.objects.get(data='data/' + file)
        file_instance.order = order
        file_instance.save()

        return redirect('/up')


def file_remove(request, file):
    print('Remove | ', file)
    try:

        if file[-4:] == '.pdf':
            doc = fitz.Document(os.path.join(Path(__file__).resolve().parent.parent.parent, 'data', file))
            pages = len(doc)
            doc.close()
            if pages > 0:
                for p in range(pages):
                    if os.path.exists(
                            os.path.join(Path(__file__).resolve().parent.parent.parent, 'data',
                                         file[:-3] + str(p) + '.jpg')):
                        os.remove(
                            os.path.join(Path(__file__).resolve().parent.parent.parent, 'data',
                                         file[:-3] + str(p) + '.jpg'))
            else:
                os.remove(
                    os.path.join(Path(__file__).resolve().parent.parent.parent, 'data', file[:-3] + str(0) + '.jpg'))
    except Exception as e:
        print(e)
    file_instance = upload_file.objects.get(data='data/' + file)
    file_instance.delete()

    return redirect('/up')


supported_formats = ['jpg', 'jpeg', 'gif', 'png', 'apng', 'svg', 'bmp']

try:
    if not TV_State.objects.filter(id=1).exists():
        TV_State.objects.create(id=1, state=1)


except Exception:
    pass

def file_upload(request):
    global Refresh_req, state_tv_r_v

    if request.method == 'POST':

        if 'tv_state_c' in request.POST:
            settings = TV_State.objects.get(id=1)
            l_state = int(settings.state)
            settings.state = request.POST['tv_state_c']
            settings.start_time = request.POST['start_time']
            settings.stop_time = request.POST['stop_time']

            settings.save()

            if time_checker_thread:
                time_checker_thread.update_times(
                    start_time=datetime.datetime.strptime(settings.start_time, '%H:%M').time(),
                    end_time=datetime.datetime.strptime(settings.stop_time, '%H:%M').time())
            # print(l_state, settings.state)
            # if l_state != int(settings.state):
            #     if int(settings.state) == 1:
            #         print('RADIO und INFO')
            #         set_mode(1)
            #
            #     elif int(settings.state) == 2:
            #         print('only radio')
            #         set_mode(2)
            #
            #     elif int(settings.state) == 3:
            #         print('onlyinfo')
            #         set_mode(3)

            Refresh_req = True

        form = ResumeUpload(request.POST, request.FILES)
        files = request.FILES.getlist('file')
        try:
            if form.is_valid():
                executor = ThreadPoolExecutor()

                for f in files:

                    if not upload_file.objects.filter(name=f).exists():
                        print('Upload |', f)
                        file_instance = upload_file(data=f, name=f)

                        file_instance.save()
                        executor.submit(update_live_folder, str(file_instance.data)[5:])
                print(os.listdir('/home/tcl/InfoDisplay/data'))
        except Exception as e:
            print(e)

    else:
        form = ResumeUpload()

    imgs_Dat = list(upload_file.objects.values('data', 'name', 'order'))
    settings = TV_State.objects.get(id=1)
    context = {'form': form, 'img_dat': imgs_Dat,
               'settings': {'state': settings.state,
                            'start': settings.start_time.strftime('%H:%M'),
                            'stop': settings.stop_time.strftime('%H:%M')}}
    # print(context)
    return render(request, 'file_upload.html', context)


def get_sorted_images():
    imgs_Dat = list(upload_file.objects.values('data', 'order'))
    newlist = sorted(imgs_Dat, key=lambda d: d['order'])

    pdf_jpgs = []
    dels = []

    current_order = -1
    for img in range(len(newlist)):
        current_order += 1
        if newlist[img]['data'][-3:] == 'pdf':

            doc = fitz.Document(
                os.path.join(Path(__file__).resolve().parent.parent.parent, 'data', newlist[img]['data'][5:]))
            pages = len(doc)
            doc.close()

            if pages == 1:
                pdf_jpgs.append({'data': newlist[img]['data'][5:-3] + str(0) + '.jpg', 'order': current_order})
            else:
                for i in range(pages):
                    a = {'data': newlist[img]['data'][5:-3] + str(i) + '.jpg', 'order': current_order}
                    pdf_jpgs.append(a)
                    current_order += 1

            dels.append(img)

        else:

            newlist[img]['order'] = current_order

    for index in sorted(dels, reverse=True):
        del newlist[index]

    for i in pdf_jpgs:
        newlist.append(i)

    return newlist

def power_off():
    dat = TV_State.objects.get(id=1)
    dat.tv_power_tgl = False
    dat.save()

def power_on():
    dat = TV_State.objects.get(id=1)
    dat.tv_power_tgl = True
    dat.save()

def tv(request, in_State):

    # state_tv_r_v = get_state_TV()
    # print('ststs',state_tv_r_v)
    if in_State == 0:

        if state_tv_r_v:
            state = '1'
        else:
            state = '0'
        return HttpResponse(state)
    else:
        # com_thread('power')
        return redirect('/')


def check_re(request):
    global Refresh_req
    global time_checker_thread
    if not time_checker_thread:
        settings = TV_State.objects.get(id=1)
        print('Thrradstart')
        time_checker_thread = TimeCheckerThread(settings.start_time, settings.stop_time)
        time_checker_thread.start()
    if Refresh_req:
        print('reoad sent')
        Refresh_req = False
        return HttpResponse('reload')
    return HttpResponse('')


sw_time = 5000


def change_sw_time(request, time):
    global sw_time
    if time == 0:
        return HttpResponse(sw_time)
    sw_time = time
    return HttpResponse('')


import logging

time_checker_thread = None


def home(request):
    # settings = TV_State.objects.get(id=1)
    # if int(settings.state) == 1:
    #     print('RADIO und INFO')
    #     radio_and_info()
    #
    # elif int(settings.state) == 2:
    #     print('only radio')
    #     only_radio()
    #
    # elif int(settings.state) == 3:
    #     print('onlyinfo')
    #     only_info()

    return render(request, 'home.html', {'img_dat': get_sorted_images(), 'time': sw_time})
