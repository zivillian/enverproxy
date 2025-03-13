#!/usr/bin/python3
# This is a simple port-forward / proxy for EnvertecBridge

import argparse
import ast
import configparser
import errno
import json
import os
import paho.mqtt.client as mqtt
import select
import socket
import signal
import sys
import syslog
import time
from datetime import datetime
from slog import slog

argparser = argparse.ArgumentParser("Enverproxy");
argparser.add_argument("--config", help="Path to config.", type=str, default="/etc/enverproxy.conf")
args = argparser.parse_args()

config = configparser.ConfigParser()
config['internal']={}
config['internal']['conf_file'] = args.config
config['internal']['section']   = 'enverproxy'
config['internal']['version']   = '1.3'
config['internal']['keys']      = "['buffer_size', 'delay', 'listen_port', 'verbosity', 'log_type', 'log_address', 'log_port', 'forward_IP', 'forward_port', 'mqttuser', 'mqttpassword', 'mqtthost', 'mqttport']"


class Forward:
    def __init__(self, l=None):
        if l == None:
            self.__log = slog('Forward class')
        else:
            self.__log = l    
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        if (host == None or port == None or host == 'None'):
            return False
        try:
            self.forward.connect((host, port))
            return self.forward
        except OSError as e:
            self.__log.logMsg('Forward produced error: ' + str(e))
            return False


class TheServer:
    input_list = []
    channel = {}

    def __init__(self, host, port, forward_to, delay = 0.0001, buffer_size = 4096, log = None):
        if log == None:
            self.__log = slog('TheServer class')
        else:
            self.__log = log
        self.__delay       = delay
        self.__buffer_size = buffer_size
        self.__forward_to  = forward_to
        self.__port        = port
        self.__host        = host
        self.server        = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def connect_mqtt(self, host, user, password, port):
        self.mqtt = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, client_id='enverproxy')
        if (user != None or password != None):
            self.mqtt.username_pw_set(user, password)
        self.mqtt.connect(host, port)

    def main_loop(self):
        self.input_list.append(self.server)
        self.__log.logMsg('Starting mqtt loop', 5)
        self.mqtt.loop_start()
        self.__log.logMsg('mqtt loop started', 5)
        while True:
            self.__log.logMsg('Entering main loop', 5)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            self.__log.logMsg('Inputready: ' + str(inputready), 3)
            for self.s in inputready:
                if self.s == self.server:
                    # proxy server has new connection request
                    self.on_accept()
                    continue
                # get the data
                try:
                    self.data = self.s.recv(self.__buffer_size)
                    self.__log.logMsg('Main loop: ' + str(len(self.data)) + ' bytes received from ' + str(self.s.getpeername()), 4)
                    if not self.data or len(self.data) == 0:
                        # Client closed the connection
                        self.on_close(self.s)
                        continue
                    else:
                        self.on_recv()
                except OSError as e:
                    self.__log.logMsg('Main loop socket error: ' + str(e), 3)
                    time.sleep(1) 
                    if e.errno in (errno.ENOTCONN, errno.ECONNRESET):
                        # Connection was closed abnormally
                        self.on_close(self.s)
                else:
                    continue

    def on_accept(self):
        self.__log.logMsg('Entering on_accept', 5)
        forward = Forward(self.__log).start(self.__forward_to[0], self.__forward_to[1])
        clientsock, clientaddr = self.server.accept()
        self.__log.logMsg(str(clientaddr) + ' has connected', 3)
        self.input_list.append(clientsock)
        if forward:
            self.input_list.append(forward)
            self.__log.logMsg('New connection list: ' + str(self.input_list), 5)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
            self.__log.logMsg('New channel dictionary: ' + str(self.channel), 5)
        else:
            time.sleep(0.4)
            self.__log.logMsg('New connection list: ' + str(self.input_list), 5)

    def on_close(self, in_s):
        self.__log.logMsg('Entering on_close with ' + str(in_s), 5)
        self.__log.logMsg('Connection list: ' + str(self.input_list), 5)
        self.__log.logMsg('Channel dictionary: ' + str(self.channel), 5)
        if in_s == self.input_list[0]:
            # First connection  cannot be closed: proxy listening on its port
            self.__log.logMsg('No connection left to close', 4)
        else:
            try:
                self.__log.logMsg('Trying to close ' + str(in_s), 5)
                self.__log.logMsg(str(in_s.getpeername()) + " has disconnected", 3)
                # close the connection with client
                in_s.close()
            except OSError as e:
                self.__log.logMsg('On_close socket error with ' + str(in_s) + ': ' + str(e), 2, syslog.LOG_ERR)
            self.input_list.remove(in_s)
            if in_s in self.channel:
                out_s = self.channel[in_s]
                try:
                    self.__log.logMsg('Trying to close ' + str(out_s), 5)
                    self.__log.logMsg('Closing connection to remote server ' + str(out_s.getpeername()), 2)
                    # close the connection with remote server
                    out_s.close()
                except OSError as e:
                    self.__log.logMsg('On_close socket error with ' + str(out_s) + ': ' + str(e), 2, syslog.LOG_ERR)
                #remove objects from input_list
                self.input_list.remove(out_s)
                self.__log.logMsg('Remaining connection list: ' + str(self.input_list), 5)
                # delete both objects from channel dict
                del self.channel[in_s]
                del self.channel[out_s]
            self.__log.logMsg('Remaining channel dictionary: ' + str(self.channel), 5)
        
    def close_all(self):
        # Close all connections
        self.__log.logMsg('Entering close_all', 5)
        self.mqtt.loop_stop()
        if len(self.input_list) > 1:
            # First connection cannot be closed: proxy listening on its port
            ilist = self.input_list[1:]
            self.__log.logMsg('Connections to close: ' + str(self.input_list), 4)
            for con in ilist:
                self.on_close(con)

    def extract(self, data, wrind):
        pos1 = 40 + (wrind*64)
        # Extract information from bytearray
        #               1        2                    4        4    5    5    6        6    7    7 
        # 0      6      2        0                    0        8    2    6    0        8    2    6
        # -------------------------------------------------------------------------------------------
        # cmd    cmd    account                       wrid     ?    dc   pwr  totalkWh temp ac   F
        # -------------------------------------------------------------------------------------------
        # 6803d6 681004 yyyyyyyy 00000000000000000000 xxxxxxxx 2202 40d0 352b 001c5f39 1d66 3872 3204
        #
        d_wr_id         = data[pos1:pos1+8]
        d_hex_dc        = data[pos1+12:pos1+12+4]
        d_hex_power     = data[pos1+16:pos1+16+4]
        d_hex_total     = data[pos1+20:pos1+20+8]
        d_hex_temp      = data[pos1+28:pos1+28+4]
        d_hex_ac        = data[pos1+32:pos1+32+4]
        d_hex_freq      = data[pos1+36:pos1+36+4]
        d_hex_remaining = data[pos1+40:pos1+40+24]
        # Calculation
        d_dez_dc    = int(d_hex_dc, 16)/512
        d_dez_power = int(d_hex_power, 16)/64
        d_dez_total = int(d_hex_total, 16)/8192
        d_dez_temp  = ((int(d_hex_temp[0:2], 16)*256+int(d_hex_temp[2:4], 16))/ 128)-40
        d_dez_ac    = int(d_hex_ac, 16)/64
        d_dez_freq  = int(d_hex_freq[0:2], 16)+int(d_hex_freq[2:4], 16)/ 256
        # Ignore if converter id is zero
        if int(d_wr_id, base=16) != 0:
            result = {'wrid' : d_wr_id, 'dc' : d_dez_dc, 'power' : d_dez_power, 'totalkwh' : d_dez_total, 'temp' : d_dez_temp, 'ac' : d_dez_ac, 'freq' : d_dez_freq, 'remaining' : d_hex_remaining}
            return result

    def submit_data(self, wrdata):
        # Can be https as well. Also: if you use another port then 80 or 443 do not forget to add the port number.
        # user and password.
        for wrdict in wrdata:
            id = wrdict.pop('wrid')
            wrdict.pop('remaining', None)
            self.__log.logMsg('Submitting data for converter: ' + str(id) + ' to MQTT', 3)
            self.mqtt.publish('enverbridge/' + id, json.dumps(wrdict))
        self.__log.logMsg('Finished sending to MQTT', 2)

    def process_data(self, data):
        datainhex = data.hex()
        wr = []
        wr_index = 0
        wr_index_max = 20
        self.__log.logMsg("Processing Data", 5)
        while True:
            response = self.extract(datainhex, wr_index)
            if response:
                self.__log.logMsg('Decoded data from microconverter with ID ' + str(response['wrid']), 2)
                wr.append(response)
            wr_index += 1
            if wr_index >= wr_index_max:
                break
        self.__log.logMsg('Finished processing data for ' + str(len(wr)) + ' microconverter: ' + str(wr), 4)
        self.__log.logMsg('Processed data for ' + str(len(wr)) + ' microconverter', 3)
        self.submit_data(wr)

    def handshake(self, data):
        data = bytearray(data)
        # Microconverter starts with 680030681006
        if data[:6].hex() == '680030681006':
            # microconverter expects reply starting with 680030681007
            data[5] = 7
            return data
        else:
            self.__log.logMsg('Microconverter sent wrong start sequence ' + str(data[:6].hex()), 2)

    def on_recv(self):
        data = self.data
        self.__log.logMsg(str(len(data)) + ' bytes in on_recv', 4)
        self.__log.logMsg('Data received as hex: ' + str(data.hex()), 2)
        if self.s.getsockname()[1] == self.__port:
            # receving data from a client
            self.__log.logMsg('Data is coming from a client', 5)
            if data[:6].hex() == '680030681006':
                # converter initiates connection
                # create reply packet
                reply = self.handshake(data)
                # This part is simulating handshake with envertecportal.com
                # disable if working as proxy between Enverbridge and envertecportal.com
                self.__log.logMsg('Replying to handshake with data ' + str(reply.hex()), 4)
                self.s.send(reply)
                self.__log.logMsg('Reply sent to: ' + str(self.s), 3)
                data = json.dumps({"ip":self.s.getpeername()[0], "last_seen":datetime.utcnow().isoformat()})
                self.mqtt.publish('enverbridge/bridge', data)
            elif data[:6].hex() in ['6803d6681004', '680056681004']:
                # payload from converter
                self.process_data(data)
            else:
                self.__log.logMsg('Client sent message with unknown content and length ' + str(len(data)), 2, syslog.LOG_ERR)
        # forward data to proxy peer
        if self.s in self.channel:
            self.channel[self.s].send(data)
            self.__log.logMsg('Data forwarded to: ' + str(self.channel[self.s]), 3)


class Signal_handler:
    def __init__(self, server, log = None):
        if log == None:
            self.__log = slog('Signal_handler class')
        else:
            self.__log = log
        self.__server = server
            
    def sigterm_handler(self, signal, frame):
        self.__log.logMsg('Received SIGTERM, closing connections', 2)
        self.__server.close_all()
        self.__log.logMsg('Stopping server', 1)
        sys.exit(0)


if __name__ == '__main__':
    # Initial verbositiy level is always 2
    # Start logging to std.out by default and until config is read 
    log = slog('Envertec Proxy', verbosity = 2, log_type='sys.stdout')
    # Get configuration data
    if os.path.isfile(config['internal']['conf_file']):
       config.read(config['internal']['conf_file'])
       section = config['internal']['section']
       if section not in config:
           log.logMsg('Section ' + section + ' is missing in config file ' + config['internal']['conf_file'], 2)
           log.logMsg('Stopping server', 1)
           sys.exit(1)
       for k in ast.literal_eval(config['internal']['keys']):
           if k not in config[section]:
               log.logMsg('Config variable "' + k + '" is missing in config file ' + config['internal']['conf_file'], 2)
               log.logMsg('Stopping server', 1)
               sys.exit(1)
    else:
        log.logMsg('Configuration file ' + config['internal']['conf_file'] + ' not found', 2)
        log.logMsg('Stopping server', 1)
        sys.exit(1)
    # Process configuration data
    verbosity   = int(config['enverproxy']['verbosity'])
    log_type    = config['enverproxy']['log_type']
    log_address = config['enverproxy']['log_address']
    log_port    = int(config['enverproxy']['log_port'])
    log         = slog('Envertec Proxy', verbosity, log_type, log_address, log_port)
    forward_to  = (config['enverproxy']['forward_IP'], int(config['enverproxy']['forward_port']))
    delay       = float(config['enverproxy']['delay'])
    buffer_size = int(config['enverproxy']['buffer_size'])
    port        = int(config['enverproxy']['listen_port'])
    server      = TheServer(host = '', port = port, forward_to = forward_to, delay = delay, buffer_size = buffer_size, log = log)
    server.connect_mqtt(config['enverproxy']['mqtthost'], config['enverproxy']['mqttuser'], config['enverproxy']['mqttpassword'], int(config['enverproxy']['mqttport']))
    # Catch SIGTERM signals    
    signal.signal(signal.SIGTERM, Signal_handler(server, log).sigterm_handler)
    # Start proxy server
    log.logMsg('Starting server (v' + config['internal']['version'] + ')', 1)
    try:
        server.main_loop()
    except KeyboardInterrupt:
        log.logMsg('Ctrl-C received, closing connections', 2)
        server.close_all()
        log.logMsg('Stopping server', 1)
        sys.exit(0)
