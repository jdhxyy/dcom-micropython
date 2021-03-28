"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
公共模块
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.protocol import *

import time


class LoadParam:
    """
    载入参数
    """

    def __init__(self):
        # 块传输帧重试间隔.单位:ms
        self.block_retry_interval = 0
        # 块传输帧重试最大次数
        self.block_retry_max_num = 0

        # API接口
        # 是否允许发送.函数原型:func(pipe: int) bool
        self.is_allow_send = None  # Callable[[int], bool]
        # 发送的是DCOM协议数据.函数原型:func(protocol: int, pipe: int, dst_ia: int, bytes: bytearray)
        self.send = None  # Callable[[int, int, int, bytearray], None]


_token = 0
_load_param = LoadParam()


def get_token():
    """
    获取token.token范围:0-1023
    :return:
    """
    global _token
    _token += 1
    if _token > 1023:
        _token = 0
    return _token


def control_word_to_bytes(word: ControlWord) -> bytearray:
    """
    控制字转换为字节流.字节流是大端顺序
    """
    value = (word.code << 29) + (word.block_flag << 28) + (word.rid << 18) + (word.token << 8) + word.payload_len
    data = bytearray()
    data.append((value >> 24) & 0xff)
    data.append((value >> 16) & 0xff)
    data.append((value >> 8) & 0xff)
    data.append(value & 0xff)
    return data


def bytes_to_control_word(data: bytearray) -> (ControlWord, bool):
    """
    字节流转控制字.字节流是大端顺序
    """
    if len(data) < CONTROL_WORD_LEN:
        return ControlWord(), False

    word = ControlWord()
    word.code = (data[0] >> 5) & 0x7
    word.block_flag = (data[0] >> 4) & 0x1
    word.rid = ((data[0] & 0xf) << 6) + ((data[1] >> 2) & 0x3f)
    word.token = (data[1] & 0x3 << 8) + data[2]
    word.payload_len = data[3]
    return word, True


def frame_to_bytes(frame: Frame) -> bytearray:
    """
    将帧转换为字节流.字节流是大端顺序
    """
    data = bytearray()
    data += control_word_to_bytes(frame.control_word)
    data += frame.payload
    return data


def bytes_to_frame(data: bytearray) -> (Frame, bool):
    """
    字节流转换为帧.字节流是大端顺序
    """
    word, err = bytes_to_control_word(data)
    if not err:
        return Frame(), False
    if len(data) < CONTROL_WORD_LEN + word.payload_len:
        return Frame(), False

    frame = Frame()
    frame.control_word = word
    frame.payload = data[CONTROL_WORD_LEN:CONTROL_WORD_LEN + word.payload_len]
    return frame, True


def block_header_to_bytes(header: BlockHeader) -> bytearray:
    """
    块传输头部转换为字节流
    """
    data = bytearray()
    data.append((header.crc16 >> 8) & 0xff)
    data.append(header.crc16 & 0xff)
    data.append((header.total >> 8) & 0xff)
    data.append(header.total & 0xff)
    data.append((header.offset >> 8) & 0xff)
    data.append(header.offset & 0xff)
    return data


def bytes_to_block_header(data: bytearray) -> (BlockHeader, bool):
    """
    字节流转块传输头部
    """
    if len(data) < BLOCK_HEADER_LEN:
        return BlockHeader(), False
    header = BlockHeader()
    j = 0
    header.crc16 = (data[j] << 8) + data[j + 1]
    j += 2
    header.total = (data[j] << 8) + data[j + 1]
    j += 2
    header.offset = (data[j] << 8) + data[j + 1]
    j += 2
    return header, True


def block_frame_to_bytes(frame: BlockFrame) -> bytearray:
    """
    块传输帧转字节流.字节流是大端顺序
    """
    data = bytearray()
    data += control_word_to_bytes(frame.control_word)
    data += block_header_to_bytes(frame.block_header)
    data += frame.payload
    return data


def bytes_to_block_frame(data: bytearray) -> (BlockFrame, bool):
    """
    字节流转换为块传输帧.字节流是大端顺序
    """
    word, err = bytes_to_control_word(data)  # type: ControlWord
    if not err:
        return BlockFrame(), False
    if len(data) < CONTROL_WORD_LEN + word.payload_len or word.payload_len < BLOCK_HEADER_LEN:
        return BlockFrame(), False

    block_header, err = bytes_to_block_header(data[CONTROL_WORD_LEN:])
    if not err:
        return BlockFrame(), False

    frame = BlockFrame()
    frame.control_word = word
    frame.block_header = block_header
    frame.payload = data[CONTROL_WORD_LEN + BLOCK_HEADER_LEN:CONTROL_WORD_LEN + word.payload_len]
    return frame, True


def get_time():
    """
    获取当前时间.单位:us
    """
    second = time.time()
    us = time.ticks_us() % 1000
    return second * 1000000 + us


def addr_to_pipe(ip: str, port: int) -> int:
    """
    网络地址转换为端口号
    转换规则为端口号+ip地址.大端排列
    """
    arr = inet_aton(ip)
    pipe = (arr[0] << 24) + (arr[1] << 16) + (arr[2] << 8) + arr[3]
    pipe |= (((port >> 8) & 0xff) << 40) + ((port & 0xff) << 32)
    return pipe


def inet_aton(ip_string: str) -> bytes:
    """ip地址转换为字节数组"""
    arr = bytearray()
    for i in ip_string.split('.')[::-1]:
        arr.append(int(i))
    if len(arr) != 4:
        return bytes(4)

    temp = arr[0]
    arr[0] = arr[3]
    arr[3] = temp
    temp = arr[1]
    arr[1] = arr[2]
    arr[2] = temp
    return bytes(arr)


def pipe_to_addr(ia: int) -> (str, int):
    """
    端口号转换为网络地址
    转换规则为网络端口+ip地址.大端排列
    """
    ip = bytearray()
    ip.append((ia >> 24) & 0xff)
    ip.append((ia >> 16) & 0xff)
    ip.append((ia >> 8) & 0xff)
    ip.append(ia & 0xff)

    port = (ia >> 32) & 0xffff
    return inet_ntoa(ip), port


def inet_ntoa(packed_ip: bytes) -> str:
    """字节数组转换为ip地址"""
    ip = ''
    for i in packed_ip:
        if len(ip) == 0:
            ip += str(i)
        else:
            ip += '.' + str(i)
    return ip


def set_load_param(param: LoadParam):
    """
    设置载入参数
    """
    global _load_param
    _load_param = param


def get_load_param() -> LoadParam:
    """
    获取载入参数
    """
    return _load_param
