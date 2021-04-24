"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
等待队列
Authors: jdh99 <jdh821@163.com>
"""

import dcompy.log as log

from dcompy.block_tx import *
from dcompy.system_error import *

import _thread
import uasyncio as asyncio


class _Item:
    def __init__(self):
        self.protocol = 0
        self.pipe = 0
        self.timeout = 0
        self.req = bytearray()
        self.resp = bytearray()
        # 启动时间.单位:us.用于判断是否超过总超时
        self.start_time = 0
        # 回调函数.存在则是异步调用
        self.ack_callback = None

        self.dst_ia = 0
        self.rid = 0
        self.token = 0
        self.is_rx_ack = False
        self.result = SYSTEM_OK

        # 上次发送时间戳.单位:us.用于重传
        self.last_retry_timestamp = 0
        self.retry_num = 0
        self.code = 0


_items = list()
_lock = _thread.allocate_lock()


async def waitlist_run():
    """
    模块运行.检查等待列表重发,超时等
    """
    global _lock

    while True:
        _lock.acquire()
        for item in _items:
            _retry_send(item)
        _lock.release()
        await asyncio.sleep(INTERVAL)


def _retry_send(item: _Item):
    t = get_time()
    if t - item.start_time > item.timeout:
        log.warn('wait ack timeout!task failed!token:%d', item.token)
        _items.remove(item)
        if len(item.req) > SINGLE_FRAME_SIZE_MAX:
            block_remove(item.protocol, item.pipe, item.dst_ia, item.code, item.rid, item.token)

        if item.ack_callback:
            # 回调方式
            item.ack_callback(bytearray(), SYSTEM_ERROR_RX_TIMEOUT)
        else:
            # 同步调用
            item.is_rx_ack = True
            item.result = SYSTEM_ERROR_RX_TIMEOUT
        return

    # 块传输不用此处重传.块传输模块自己负责
    if len(item.req) > SINGLE_FRAME_SIZE_MAX:
        return

    load_param = get_load_param()
    if t - item.last_retry_timestamp < load_param.block_retry_interval * 1000:
        return

    # 重传
    item.retry_num += 1
    if item.retry_num >= load_param.block_retry_max_num:
        log.warn('retry too many!task failed!token:%d', item.token)
        _items.remove(item)

        if item.ack_callback:
            # 回调方式
            item.ack_callback(bytearray(), SYSTEM_ERROR_RX_TIMEOUT)
        else:
            # 同步调用
            item.is_rx_ack = True
            item.result = SYSTEM_ERROR_RX_TIMEOUT
        return

    item.last_retry_timestamp = t
    log.warn('retry send.token:%d retry num:%d', item.token, item.retry_num)
    _send_frame(item.protocol, item.pipe, item.dst_ia, item.code, item.rid, item.token, item.req)


def call(protocol: int, pipe: int, dst_ia: int, rid: int, timeout: int, req: bytearray) -> (bytearray, int):
    """
    RPC同步调用
    :param protocol: 协议号
    :param pipe: 通信管道
    :param dst_ia: 目标ia地址
    :param rid: 服务号
    :param timeout: 超时时间,单位:ms.为0表示不需要应答
    :param req: 请求数据.无数据可填bytearray()或者None
    :return: 返回值是应答字节流和错误码.错误码非SYSTEM_OK表示调用失败
    """
    global _lock

    log.info('call.protocol:%d pipe:0x%x dst ia:0x%x rid:%d timeout:%d', protocol, pipe, dst_ia, rid, timeout)
    code = CODE_CON if timeout > 0 else CODE_NON
    if not req:
        req = bytearray()

    token = get_token()
    _send_frame(protocol, pipe, dst_ia, code, rid, token, req)

    if code == CODE_NON:
        return bytearray(), SYSTEM_OK

    item = _Item()
    item.protocol = protocol
    item.pipe = pipe
    item.timeout = timeout * 1000
    item.req = req
    item.start_time = get_time()

    item.dst_ia = dst_ia
    item.rid = rid
    item.token = token
    item.code = code

    item.retry_num = 0
    item.last_retry_timestamp = get_time()

    _lock.acquire()
    _items.append(item)
    _lock.release()

    while True:
        if item.is_rx_ack:
            break

    log.info('call resp.result:%d len:%d', item.result, len(item.resp))
    return item.resp, item.result


def call_async(protocol: int, pipe: int, dst_ia: int, rid: int, timeout: int, req: bytearray, ack_callback):
    """
    RPC异步调用
    :param protocol: 协议号
    :param pipe: 通信管道
    :param dst_ia: 目标ia地址
    :param rid: 服务号
    :param timeout: 超时时间,单位:ms.为0表示不需要应答
    :param req: 请求数据.无数据可填bytearray()或者None
    :param ack_callback: 回调函数.原型func(resp: bytearray, error: int).参数是应答字节流和错误码.错误码非SYSTEM_OK表示调用失败
    """
    global _lock

    code = CODE_CON
    if timeout == 0 or not callable(ack_callback):
        code = CODE_NON
    if not req:
        req = bytearray()

    token = get_token()
    log.info('call async.token:%d protocol:%d pipe:0x%x dst ia:0x%x rid:%d timeout:%d', token, protocol, pipe, dst_ia,
             rid, timeout)
    _send_frame(protocol, pipe, dst_ia, code, rid, token, req)

    if code == CODE_NON:
        return

    item = _Item()
    item.ack_callback = ack_callback
    item.protocol = protocol
    item.pipe = pipe
    item.timeout = timeout * 1000
    item.req = req
    item.start_time = get_time()

    item.dst_ia = dst_ia
    item.rid = rid
    item.token = token
    item.code = code

    item.retry_num = 0
    item.last_retry_timestamp = get_time()

    _lock.acquire()
    _items.append(item)
    _lock.release()


def _send_frame(protocol: int, pipe: int, dst_ia: int, code: int, rid: int, token: int, data: bytearray):
    if len(data) > SINGLE_FRAME_SIZE_MAX:
        block_tx(protocol, pipe, dst_ia, code, rid, token, data)
        return

    frame = Frame()
    frame.control_word.code = code
    frame.control_word.block_flag = 0
    frame.control_word.rid = rid
    frame.control_word.token = token
    frame.control_word.payload_len = len(data)
    frame.payload.extend(data)
    log.info('send frame.token:%d', token)
    send(protocol, pipe, dst_ia, frame)


def rx_ack_frame(protocol: int, pipe: int, src_ia: int, frame: Frame):
    """
    接收到ACK帧时处理函数
    """
    global _lock

    _lock.acquire()

    log.info('rx ack frame.src ia:0x%x', src_ia)
    for item in _items:
        if _check_item_and_deal_ack_frame(protocol, pipe, src_ia, frame, item):
            break

    _lock.release()


def _check_item_and_deal_ack_frame(protocol: int, pipe: int, src_ia: int, frame: Frame, item: _Item) -> bool:
    if item.protocol != protocol or item.pipe != pipe or item.dst_ia != src_ia or item.rid != frame.control_word.rid \
            or item.token != frame.control_word.token:
        return False

    log.info('deal ack frame.token:%d', item.token)
    _items.remove(item)
    if item.ack_callback:
        # 回调方式
        item.ack_callback(frame.payload, SYSTEM_OK)
    else:
        # 同步调用
        item.is_rx_ack = True
        item.result = SYSTEM_OK
        item.resp = frame.payload
    return True


def rx_rst_frame(protocol: int, pipe: int, src_ia: int, frame: Frame):
    """
    接收到RST帧时处理函数
    """
    global _lock

    _lock.acquire()

    log.warn('rx rst frame.src ia:0x%x', src_ia)
    for item in _items:
        _deal_rst_frame(protocol, pipe, src_ia, frame, item)

    _lock.release()


def _deal_rst_frame(protocol: int, pipe: int, src_ia: int, frame: Frame, item: _Item):
    if item.protocol != protocol or item.pipe != pipe or item.dst_ia != src_ia or item.rid != frame.control_word.rid \
            or item.token != frame.control_word.token:
        return False
    result = frame.payload[0]
    log.warn('deal rst frame.token:%d result:0x%x', item.token, result)
    _items.remove(item)
    if item.ack_callback:
        # 回调方式
        item.ack_callback(bytearray(), result)
    else:
        # 同步调用
        item.is_rx_ack = True
        item.result = result
    return True
