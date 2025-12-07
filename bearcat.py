#!/usr/bin/env python3

import sys
import logging

from dataclasses import dataclass

import serial
import serial.tools
import serial.tools.list_ports

DEVICE_IDS = [
              "10c4:ea60", # Silicon Labs CP210x UART Bridge
             ]

SUPPORTED_MODELS = [
                    "BC75XLT",      # US/Canada
                    "UBC75XLT",     # European
                   ]

BANDPLANS = {
              '0': "US",
              '1': "Canada",
              '2': "Europe",
            }

logging.basicConfig(level=logging.DEBUG)

class Port():
    _serial: None
    def __init__(self, portname: str):
        baudrate = 57600
        self._serial = serial.Serial(portname, baudrate=baudrate)
        self._serial.timeout = 3

    def send(self, command: str):
        logging.info(f"> {command}")
        self._serial.write(f'{command}\r'.encode())

    def recv(self):
        resp = self._serial.read_until(b'\r').decode('utf-8').removesuffix('\r')
        logging.info(f"< {resp}")
        return resp

    def query(self, command: str = ''):
        self.send(command)
        return self.recv()

@dataclass
class ChannelInfo():
    ch: int
    freq: float # MHz
    mod: str
    dly: bool
    lo: bool
    prio: bool

    @classmethod
    def from_cmd(cls, resp):
        #['CIN', '295', '', '00000000', 'FM', '', '0', '1', '0']
        _, channel, _, freq10, modulation, _, delay, lockout, priority = resp

        return cls(ch=int(channel),
                   freq = int(freq10, 10) / 10000.0, # MHz
                   mod=modulation,
                   dly=bool(int(delay)),
                   lo=bool(int(lockout)),
                   prio=bool(int(priority)))

    def as_cmd(self):
        def boolchar(b):
            return '1' if b else '0'
        return ["CIN",
                f"{self.ch}",
                "",
                f"{self.freq*10000:08.0f}",
                "", # MOD - ignore input
                "", # reserved unknown
                boolchar(self.dly),
                boolchar(self.lo),
                boolchar(self.prio),
               ]

class UnidenBearcat():
    def __init__(self, serial_port: Port):
        self._port = serial_port
        self._is_prog = False

        self.query() # submit garbage from buffer

    def query(self, command: str = ''):
        return self._port.query(command)

    def cmd(self, *commands):
        return self.query(",".join(commands)).split(',')

    def ensure_program_mode(self):
        if self._is_prog:
            return
        self.query("PRG")
        self._is_prog = True

    def exit_program_mode(self):
        self.query("EPG")
        self._is_prog = False

    def get_model(self):
        raw = self.cmd('MDL')
        return raw[1]

    def get_firmware(self):
        raw = self.cmd('VER')
        return raw[1]

    def get_bandplan(self):
        self.ensure_program_mode()
        raw = self.cmd('BPL')
        return raw[1]

    def get_channel(self, channel_id: int):
        self.ensure_program_mode()
        raw = self.cmd('CIN', f"{channel_id}")
        return raw

    def self_check_model(self):
        model = self.get_model()
        assert model in SUPPORTED_MODELS, f"Unsupported model {model}"
        firmware = self.get_firmware()
        bandplan = self.get_bandplan()
        bandplan_desc = BANDPLANS[bandplan]
        print(f"{model}, {firmware}, bandplan {bandplan} ({bandplan_desc}")

    def list_channels(self):
        for i in range(1, 300+1):
            ch = self.get_channel(i)
            chi = ChannelInfo.from_cmd(ch)
            print(ch)
            print(chi)


    @classmethod
    def from_port(cls, portname: str):
        port = Port(portname)
        obj = cls(serial_port=port)
        return obj



def cmd_list_ports():
    for port in list_ports():
        print(port)

def list_ports():
    return [x.device
            for x in serial.tools.list_ports.comports()
            if x.vid is not None
            and f"{x.vid:x}:{x.pid:x}" in DEVICE_IDS]

def open_port():
    ...

def main():
    cmd_list_ports()
    portname = list_ports()[0]

    ub = UnidenBearcat.from_port(portname)
    ub.self_check_model()

    ub.list_channels()



if __name__ == "__main__":
    main()
