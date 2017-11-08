#!/usr/bin/python
## -*- coding: utf-8 -*-
__author__ = 'Coulson Sun'
import os
import datetime
import time
import serial
import logging
import urllib2, urllib, re, thread
from logging.handlers import RotatingFileHandler

#TODO: Update device list

NodeNetAddrList = []

def initlog():
    logger = logging.getLogger()
    LOG_FILE = '/var/log/mytest.log'
    hdlr = RotatingFileHandler(LOG_FILE,maxBytes=1024*1024,backupCount=10)
    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    return logger

def serial_read(length = 1):
    ser = serial.Serial("/dev/ttyUSB1", 115200, timeout=20) #Set timeout to check if the sensor is woring well.
    if (ser.isOpen()):
        while ser.inWaiting:
            data = ser.read(length)
            # Maybe need use line = ser.readline()
            #ser.flushInput() #Clear input buffer
            return data
    else:
        log.error("The serial port is disabled")
        return False

def send_alter_to_wexin(string = ''):
    print string
    NodeID = 12
    SensorWays = 3
    Status = "警报来源处检测到危险，请尽快处理！！！"
    Priority = "高"
    # url = r"http://769d380c.ngrok.io/metinfo/testForXuefeng/test.php"
    url = r"http://6ef9053c.ngrok.io/metinfo/wePHP/index.php"
    # [Coulson]: url = r"http://www.brovantek.com/wePHP/index.php"
    # [Coulson]: url = r"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx34f4411ff5e23438&secret=c6ec2ea24b77fecf919d9d0b9fbc69d8"
    user_agent = "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19"
    Content_Type = "application/x-www.form-urlencoded"
    # data = urllib.urlencode({'data1': 'www','data2':'data2'})
    xml_data = '''
            <xml>
                <NodeId>%X — %X</NodeId>
                <Status>%s</Status>
                <MsgType>zigbee</MsgType>
            </xml>'''%(NodeID, SensorWays, Status)

    headers = {'User-Agent' : user_agent, 'Content-Type': Content_Type}
    req = urllib2.Request(url, data = xml_data, headers=headers)
    response = urllib2.urlopen(req)
    if response.code != 200:
        print "An error during requesting"
        print response.code
    else:
        print "post requests successfully"
        current_page = response.read()
        print current_page



def integrate_data(rawData, length = 1):
    data = 0
    try:
        rawData.reverse()
        for i in length:
            data = data | (rawData[i] << (8 * (length - i)))
        return data
    except AttributeError, e:
        log.error(e)

def formater(data, isHeartbeat = True):
    heartbeatData = {}
    switchingValue = {}
    if isHeartbeat:
        heartbeatData["PkgType"] = "Heatbeat"
        heartbeatData["NodeNetAddr"] = integrate_data(data[3:5], 2)
        heartbeatData["NodePyAddr"] = data[5:13] #大小端未转换
        if data[13] == 0x0E:
            log.info("This is a router")
            heartbeatData["NodeType"] = "Router"
        heartbeatData["CoordinatorMac"] = data[13:21]
        if heartbeatData["NodeNetAddr"] not in NodeNetAddrList:
            NodeNetAddrList.append(heartbeatData["NodeNetAddr"])
            string = "New device %s join in ... "%hex(heartbeatData["NodeNetAddr"])
            log.info(string)
            send_alter_to_wexin(string)
        return heartbeatData
    else:
        switchingValue["PkgType"] = "Switching"
        switchingValue["NodeNetAddr"] = integrate_data(data[4:6], 2)
        switchingValue["Ways"] = data[6]
        switchingValue["Status"] = data[-2]
        log.info("This is an endpoint")
        return switchingValue

def decode_sensor_NodeId():
    startChar = serial_read(1)
    #起始符
    if startChar == 0xFF:
        #读取数据长度
        temp = serial_read(2)
        #计算数据总长度(包括起始符，数据长度，数据不包括结束符)
        dataLength = integrate_data(temp, len(temp))
        temp = serial_read(dataLength - 3)

        if temp[-1] == 0xAA: #endChar
            log.info("Data is vaild, to be decoded ...")
            if temp[2] == 0x60:
                currentValue = formater(temp, isHeartbeat = True)
            else:
                currentValue = formater(temp, isHeartbeat = False)
            return currentValue
        else:
            log.error("Data is wrong, try read again ...")
    else:
        log.error("Invalid command !")
        return None

def main():
    string = "Starting ..."
    while True:
        log.info(string)
        current_status = decode_sensor_location()
        if current_status:
            if current_status["PkgType"] == "Heatbeat":
                string = "Node %x is working well ..."%current_status["NodeNetAddr"]
            elif current_status["PkgType"] == "Switching":
                if current_status["Status"] == 0:
                    string = "Node %x is working or recoveried"%current_status["NodeNetAddr"]
                    send_alter_to_wexin(string)
                else:
                    string = "The sensor %x - %s has been assert, please pay attention ..."%(current_status["NodeNetAddr"], current_status["Ways"])
                    send_alter_to_wexin(string)
            else:
                log.info("Unknown package type.")
        else:
            log.error("No available command can be supported")

if __name__ == "__main__":
    # global log
    # log = initlog()
    # main()
    send_alter_to_wexin("start now ...")
