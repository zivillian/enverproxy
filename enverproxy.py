#!/usr/bin/python
# This is a simple port-forward / proxy, written using only the default python
# library. If you want to make a suggestion or fix something you can contact-me
# at voorloop_at_gmail.com
# Distributed over IDC(I Don't Care) license
from __future__ import division
import socket
import select
import time
import sys
import os

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
buffer_size = 4096
delay = 0.0001
forward_to = ('www.envertecportal.com', 10013)
DEBUG = False

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception, e:
            print e
            return False

class TheServer:
    input_list = []
    channel = {}

    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def main_loop(self):
        self.input_list.append(self.server)
        while 1:
            time.sleep(delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                    break

                try:
                    self.data = self.s.recv(buffer_size)
                    if len(self.data) == 0:
                        self.on_close()
                        break
                    else:
                        self.on_recv()
                except socket.error:
                    if DEBUG:
                        print ('Socket error')
                        time.sleep(1) 
                    #self.on_close()
                else:
                    continue

    def on_accept(self):
        forward = Forward().start(forward_to[0], forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            print clientaddr, "has connected"
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            print "Can't establish connection with remote server.",
            print "Closing connection with client side", clientaddr
            clientsock.close()

    def on_close(self):
        print self.s.getpeername(), "has disconnected"
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def extract(self, data, wrind):
        pos1 = 40 + (wrind*64)
        # Define
        d_wr_id = data[pos1:pos1+8]
        d_hex_dc = data[pos1+12:pos1+12+4]
        d_hex_power = data[pos1+16:pos1+16+4]
        d_hex_total = data[pos1+20:pos1+20+8]
        d_hex_temp = data[pos1+28:pos1+28+4]
        d_hex_ac = data[pos1+32:pos1+32+4]
        d_hex_freq = data[pos1+36:pos1+36+4]
        d_hex_remaining = data[pos1+40:pos1+40+24]

        # Calculation
        d_dez_dc = '{0:.2f}'.format(int(d_hex_dc, 16)/512)
        d_dez_power = '{0:.2f}'.format(int(d_hex_power, 16)/64)
        d_dez_total = '{0:.2f}'.format(int(d_hex_total, 16)/8192)
        d_dez_temp = '{0:.2f}'.format(((int(d_hex_temp[0:2], 16)*256+int(d_hex_temp[2:4], 16))/ 128)-40)
        d_dez_ac = '{0:.2f}'.format(int(d_hex_ac, 16)/64)
        d_dez_freq = '{0:.2f}'.format(int(d_hex_freq[0:2], 16)+int(d_hex_freq[2:4], 16)/ 256)

        if int(d_wr_id) != 0:
            result = {'wrid' : d_wr_id, 'dc' : d_dez_dc, 'power' : d_dez_power, 'totalkwh' : d_dez_total, 'temp' : d_dez_temp, 'ac' : d_dez_ac, 'freq' : d_dez_freq, 'remaining' : d_hex_remaining}
            return result

    def submit_data(self, wrdata):
        # Can be https as well. Also: if you use another port then 80 or 443 do not forget to add the port number.
        pimatic_server = 'IP FOR PIMATIC SERVER'
        # user and password. I prefer a special posting user having a role of varposter with only  "variables": "write" in the varposter role. Rest to "none" or false.
        pimatic_user = 'removed'
        pimatic_pass = 'removed'
        pim_user_pass = pimatic_user + ':' + pimatic_pass
        curl_prefix = 'curl --silent --insecure -X PATCH --header "Content-Type:application/json" --data \'{"type": "value", "valueOrExpression": "'
        pim_server_url = pimatic_server + '/api/variables/'
        #print len(wrdata)
        #print wrdata

        for wrdict in wrdata:
            print wrdict['wrid']
            values = 'ac', 'dc', 'temp', 'power', 'totalkwh', 'freq'
            for value in values:
                os.system(curl_prefix + wrdict[value] + '"}\'  --user "' + pim_user_pass + '" ' + pim_server_url + "wrid" + wrdict['wrid'] + "_" + value)

    def process_data(self, data):
        datainhex = data.encode('hex')
        print datainhex
        wr = []
        wr_index = 0
        wr_index_max = 20
        while True:
            if DEBUG:
                print "Processing Data"
            response = self.extract(datainhex, wr_index)
            if response:
                if DEBUG:
                    print "."
                wr.append(response)
            wr_index += 1
            if wr_index >= wr_index_max:
                break
        if DEBUG:
            print "Processed Data!"
            print wr
            print "Submitting Data"
        self.submit_data(wr)

    def on_recv(self):
        data = self.data
        print len(data)
        if len(data) == 662: 
            self.process_data(data)
            #print data.encode('hex')
        self.channel[self.s].send(data)

if __name__ == '__main__':
        server = TheServer('', 10013)
        try:
            server.main_loop()
        except KeyboardInterrupt:
            print "Ctrl C - Stopping server"
            sys.exit(1)