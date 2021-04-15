"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
块传输发送模块
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.tx import *
from dcompy.common import *
from dcompy.config import *

import crcmodbus
import _thread
import uasyncio as asyncio


class _Item:
    def __init__(self):
        self.protocol = 0
        self.pipe = 0
        self.dst_ia = 0
        self.code = 0
        self.rid = 0
        self.token = 0

        # 第一帧需要重发控制
        self.is_first_frame = False
        self.first_frame_retry_time = 0
        self.first_frame_retry_num = 0

        self.last_rx_ack_time = 0

        self.crc16 = 0
        self.data = bytearray()


_items = list()
_lock = _thread.allocate_lock()


async def block_tx_run():
    """
    块传输发送模块运行
    :return:
    """
    global _lock

    while True:
        _lock.acquire()
        for item in _items:
            _check_timeout_and_retry_send_first_frame(item)
        _lock.release()

        await asyncio.sleep(INTERVAL)


def _check_timeout_and_retry_send_first_frame(item: _Item):
    now = get_time()
    load_param = get_load_param()
    if not item.is_first_frame:
        if now - item.last_rx_ack_time > load_param.block_retry_interval * load_param.block_retry_max_num * 1000:
            log.warn('block tx timeout!remove task.token:%d', item.token)
            _items.remove(item)
        return

    # 首帧处理
    if now - item.first_frame_retry_time < load_param.block_retry_interval * 1000:
        return

    if item.first_frame_retry_num >= load_param.block_retry_max_num:
        log.warn('block tx timeout!first frame send retry too many.token:%d', item.token)
        _items.remove(item)
    else:
        item.first_frame_retry_num += 1
        item.first_frame_retry_time = now
        log.info("block tx send first frame.token:%d retry num:%d", item.token, item.first_frame_retry_num)
        _block_tx_send_frame(item, 0)


def _block_tx_send_frame(item: _Item, offset: int):
    log.info('block tx send.token:%d offset:%d', item.token, offset)
    delta = len(item.data) - offset
    payload_len = SINGLE_FRAME_SIZE_MAX - BLOCK_HEADER_LEN
    if payload_len > delta:
        payload_len = delta

    frame = BlockFrame()
    frame.control_word.code = item.code
    frame.control_word.block_flag = 1
    frame.control_word.rid = item.rid
    frame.control_word.token = item.token
    frame.control_word.payload_len = BLOCK_HEADER_LEN + payload_len
    frame.block_header.crc16 = item.crc16
    frame.block_header.total = len(item.data)
    frame.block_header.offset = offset
    frame.payload.extend(item.data[offset:offset + payload_len])
    block_send(item.protocol, item.pipe, item.dst_ia, frame)


def block_tx(protocol: int, pipe: int, dst_ia: int, code: int, rid: int, token: int, data: bytearray):
    """
    块传输发送
    """
    global _lock

    if len(data) <= SINGLE_FRAME_SIZE_MAX:
        return

    _lock.acquire()

    if _is_item_exist(protocol, pipe, dst_ia, code, rid, token):
        _lock.release()
        return

    log.info('block tx new task.token:%d dst ia:0x%x code:%d rid:%d', token, dst_ia, code, rid)
    item = _create_item(protocol, pipe, dst_ia, code, rid, token, data)
    _block_tx_send_frame(item, 0)
    item.first_frame_retry_num += 1
    item.first_frame_retry_time = get_time()
    _items.append(item)

    _lock.release()


def _is_item_exist(protocol: int, pipe: int, dst_ia: int, code: int, rid: int, token: int) -> bool:
    for item in _items:
        if item.protocol == protocol and item.pipe == pipe and item.dst_ia == dst_ia and item.code == code \
                and item.rid == rid and item.token == token:
            return True
    return False


def _create_item(protocol: int, pipe: int, dst_ia: int, code: int, rid: int, token: int, data: bytearray) -> _Item:
    item = _Item()
    item.protocol = protocol
    item.pipe = pipe
    item.dst_ia = dst_ia
    item.code = code
    item.rid = rid
    item.token = token
    item.data.extend(data)
    item.crc16 = crcmodbus.checksum(data)

    item.is_first_frame = True
    item.first_frame_retry_num = 0
    now = get_time()
    item.first_frame_retry_time = now
    item.last_rx_ack_time = now
    return item


def block_rx_back_frame(protocol: int, pipe: int, src_ia: int, frame: Frame):
    """
    接收到BACK帧时处理函数
    """
    global _lock

    if frame.control_word.code != CODE_BACK:
        return

    _lock.acquire()
    for item in _items:
        if _check_item_and_deal_back_frame(protocol, pipe, src_ia, frame, item):
            break
    _lock.release()


def _check_item_and_deal_back_frame(protocol: int, pipe: int, src_ia: int, frame: Frame, item: _Item) -> bool:
    """
    checkNodeAndDealBackFrame 检查节点是否符合条件,符合则处理BACK帧
    :return: 返回true表示节点符合条件
    """
    if item.protocol != protocol or item.pipe != pipe or item.dst_ia != src_ia or \
            item.rid != frame.control_word.rid or item.token != frame.control_word.token:
        return False
    log.info('block tx receive back.token:%d', item.token)
    if frame.control_word.payload_len != 2:
        log.warn('block rx receive back deal failed!token:%d payload len is wrong:%d', item.token,
                 frame.control_word.payload_len)
        return False
    start_offset = (frame.payload[0] << 8) + frame.payload[1]
    if start_offset >= len(item.data):
        # 发送完成
        log.info('block tx end.receive back token:%d start offset:%d >= data len:%d"', item.token, start_offset,
                 len(item.data))
        _items.remove(item)
        return True

    if item.is_first_frame:
        item.is_first_frame = False
    item.last_rx_ack_time = get_time()

    _block_tx_send_frame(item, start_offset)
    return True


def block_tx_deal_rst_frame(protocol: int, pipe: int, src_ia: int, frame: Frame):
    """
    块传输发送模块处理复位连接帧
    """
    global _lock

    _lock.acquire()
    for item in _items:
        if item.protocol == protocol and item.pipe == pipe and item.dst_ia == src_ia \
                and item.rid == frame.control_word.rid and item.token == frame.control_word.token:
            log.warn('block tx receive rst.token:%d', item.token)
            _items.remove(item)
            break
    _lock.release()


def block_remove(protocol: int, pipe: int, dst_ia: int, code: int, rid: int, token: int):
    """块传输发送移除任务"""
    _lock.acquire()
    for item in _items:
        if item.protocol == protocol and item.pipe == pipe and item.dst_ia == dst_ia and item.code == code and \
                item.rid == rid and item.token == token:
            log.warn('block tx remove task.token:%d', item.token)
            _items.remove(item)
            break
    _lock.release()
