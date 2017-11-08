#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Coulson Sun'
import os
import datetime
import time
import serial
import logging
import urllib2, urllib, re, thread
import json, threading
from logging.handlers import RotatingFileHandler
from threading import Timer

Path = '/etc/zigbee/roommap.json'

NodeNetAddrList = [00]
DeviceMap = {}
RoomMap = {}
Buffer = []
lock = threading.Lock()


def load():
    try:
        with open(Path) as json_file:
            data = json.load(json_file)
            return data
    except ValueError,e:
        return  RoomMap
        log.error("roommap.Json file is None, %s"%e)

def store(data):
    with open(Path, 'w') as json_file:
        json_file.write(json.dumps(data))

def initlog():
    logger = logging.getLogger()
    LOG_FILE = '/var/log/mytest.log'
    hdlr = RotatingFileHandler(LOG_FILE,maxBytes=1024*1024,backupCount=10)
    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    return logger

class Sensor(object):
    """docstring for Sensor"""
    def __init__(self, **kw):
        super(Sensor, self).__init__()
        self._nodeid = hex(kw['NodeNetAddr'])  #convert address to str... ex. 123 as '0x7b'
        self._ways = kw['Ways']
        self._status = kw['Status']
    
    def get_status(self):
        return self._status

    def get_location(self):
        '''
        Status Description:
        0   :   Assert
        1   :   De-assert
        2   :   Established
        3   :   Disconnect
        '''
        log.info("NodeID:%s  SensorWays:%s  Status:%s"%(self._nodeid, self._ways, self._status))
        try:
            if self._status == 0 or self._status == 1:
                location = "%s - 第 %s 路"%(RoomMap[self._nodeid].encode("utf8"), self._ways)
            elif self._status == 2 or self._status == 3:
                location = "%s "%RoomMap[self._nodeid].encode("utf8")
            return location
        except Exception, e:
            log.error("Cannot find this room, please reconfig /etc/zigbee/roommap.json, Exception: %s"%e)
            RoomNumber = len(RoomMap) + 1
            location = "节点地址 %s, 分配房间号 %s"%(self._nodeid, RoomNumber)
            RoomMap[self._nodeid] = "房间%s".decode("utf8")%RoomNumber
            store(RoomMap)
            return location
 

    def send_to_weixin(self):
        #Prepare parameter for structuring a XML data.
        if self._status == 0:
            Status = "警报来源处检测到危险，请尽快处理！！！"
            Priority = "高"
        elif self._status == 1:
            Status = "警报解除！！！"
            Priority = "低"
        elif self._status == 2:
            Status = "新建连接"
            Priority = "低"
        elif self._status == 3:
            Status = "断开连接"
            Priority = "高"
        else:
            Status = "未知情况"
            Priority = "未知情况"
        #muban XML structure
        url = r"http://www.brovantek.com/wePHP/index.php"
        user_agent = "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19"
        Content_Type = "application/x-www.form-urlencoded"
        xml_data = '''
                <xml>
                    <Header>尊敬的博砚电子用户： \n\r以下是报警装置最新状态，请及时采取措施！</Header>
                    <Location>%s</Location>
                    <Status>%s</Status>
                    <Priority>%s</Priority>
                    <MsgType>zigbee</MsgType>
                    <Remark>\n\r*** 欢迎使用， 谢谢！***</Remark>
                </xml>'''%(self.get_location(), Status, Priority)
        log.info(xml_data)
        print xml_data # debug code
        return 0 # debug code
        headers = {'User-Agent' : user_agent, 'Content-Type': Content_Type}
        req = urllib2.Request(url, data = xml_data, headers=headers)
        response = urllib2.urlopen(req)
        if response.code != 200:
            log.error("An error during requesting, then retry to send Respense.code: %s"%response.code)
            Timer(10, self.send_to_weixin).start() #10 sec
        else:
            log.error("post requests successfully")
            current_page = response.read()
            log.info("current_page: \n\r", current_page)

class Transaction(object):
    """docstring for Transaction"""
    def __init__(self):
        super(Transaction, self).__init__()

    #This code cannot working, so far I don't know why
    def _serial_read(self, device = "/dev/ttyUSB0", baud = 115200, length = 1):
        ser = serial.Serial(device, baud) #Set timeout to check if the sensor is working well.
        if (ser.isOpen()):
            while ser.inWaiting:
                data = ser.read(length)
                # Maybe need use line = ser.readline()
                #ser.flushInput() #Clear input buffer
                return data
        else:
            log.error("The serial port is disabled")
            return False
        
    def _address_decode(self, data, isHeartbeat = True):
        heartbeatData = {}
        switchingValue = {}
        if isHeartbeat:
            heartbeatData["PkgType"] = "Heartbeat"
            heartbeatData["NodeNetAddr"] = self._swap_data(data[3:5], 2)
            if data[13] == '\x0e':
                log.info("This is a router")
            if heartbeatData["NodeNetAddr"] not in NodeNetAddrList:
                lock.acquire()
                NodeNetAddrList.append(heartbeatData["NodeNetAddr"])
                lock.release()
                string = "New device %s join in ... "%hex(heartbeatData["NodeNetAddr"])
                log.info(string)
                heartbeatData['Ways'] = 0
                heartbeatData['Status'] = 2
                s = Sensor(**heartbeatData)
                s.send_to_weixin()
            return heartbeatData
        else:
            switchingValue["PkgType"] = "Switching"
            switchingValue["NodeNetAddr"] = self._swap_data(data[4:6], 2)
            switchingValue["Ways"] = ord(data[6])
            switchingValue["Status"] = ord(data[-2])
            log.info("This is an endpoint")
            return switchingValue

    def _swap_data(self, rawData, length = 1):
        data = 0
        l = list(rawData)
        try:
            l.reverse()
            for i in range(length):
                data = data | (ord(l[i]) << (8 * (length - i - 1)))
            return data
        except AttributeError, e:
            log.error(e)

    def recive_data(self):
        #startChar = self._serial_read(length = 1)
        ser = serial.Serial('/dev/ttyUSB0', 115200)
        startChar = ser.read(1)
        #起始符
        if startChar == '\xfe':
            #读取数据长度
            temp = ser.read(2)
            # temp = self._serial_read(length = 2)
            #计算数据总长度(包括起始符，数据长度，数据不包括结束符)
            dataLength = self._swap_data(temp, len(temp))
            #debug
            temp = ser.read(dataLength - 3)
            # temp = self._serial_read(length = dataLength - 3)

            if temp[-1] == '\xaa': #endChar
                log.info("Data is valid, to be decoded ...")
                if temp[2] == '\x60':
                    currentValue = self._address_decode(temp, isHeartbeat = True)
                else:
                    currentValue = self._address_decode(temp, isHeartbeat = False)
                return currentValue
            else:
                log.error("Data is wrong, try read again ...")
                return None
        else:
            log.error("Invalid command !")
            return None

def monitor_task():
    dic = {}
    try:
        lock.acquire()
        log.info("Buffer: %s NodeNetAddrList: %s"%(Buffer, NodeNetAddrList))
        if len(list(set(Buffer))) < len(list(set(NodeNetAddrList))):
            #Here, means that some device is disconnected. Report this event to user by weixin.
            DisconnectList = list(set(NodeNetAddrList).difference(set(Buffer)))
            log.error("DisconnectList: %s"%DisconnectList)
            for d in DisconnectList:
                if d:
                    dic['NodeNetAddr'] = d
                    dic['Ways'] = 0
                    dic['Status'] = 3
                    s = Sensor(**dic)
                    s.send_to_weixin()
                    NodeNetAddrList.remove(d)
    finally:
        #Clear Buffer for next checking
        del Buffer[:]
        Timer(60 * 4, monitor_task).start() #Checking window: 4 mins
        lock.release()

def main():
    t = Transaction()
    string = "Starting ..."
    while True:
        log.info(string)
        current_status = t.recive_data()
        if current_status:
            if current_status["PkgType"] == "Heartbeat":
                string = "Node %s is working well ..."%hex(current_status["NodeNetAddr"])
                #Push devices in buffer for other threading to regular checking and make sure all devices are working well,
                #once one of device disconnect, will signal alert event to weixin.
                lock.acquire()
                Buffer.append(current_status["NodeNetAddr"])
                lock.release()
            elif current_status["PkgType"] == "Switching":
                if current_status["Status"] == 0:
                    string = "Node %s is working or recovered"%hex(current_status["NodeNetAddr"])
                    s = Sensor(**current_status)
                    s.send_to_weixin()
                else:
                    string = "The sensor %s - %s has been assert, please pay attention ..."%(hex(current_status["NodeNetAddr"]), current_status["Ways"])
                    s = Sensor(**current_status)
                    s.send_to_weixin()
            else:
                log.info("Unknown package type.")
        else:
            log.error("No available command can be supported")

if __name__ == "__main__":
    global log
    log = initlog()
    RoomMap = load()
#    m = threading.Thread(target=monitor_task)
    #A threading to check if all devices are working well
    t = Timer(60 * 4, monitor_task) #10 sec
    t.start()
    main()
