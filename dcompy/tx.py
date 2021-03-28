"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
发送模块
Authors: jdh99 <jdh821@163.com>
"""

import dcompy.log as log

from dcompy.common import *


def send(protocol: int, pipe: int, dst_ia: int, frame: Frame):
    """
    发送数据
    """
    if frame is None:
        return

    load_param = get_load_param()
    if not load_param.is_allow_send(pipe):
        log.warn('send failed!pipe:0x%x is not allow send.token:%d', pipe, frame.control_word.token)
        return
    log.info('send frame.token:%d protocol:%d pipe:0x%x dst ia:0x%x', frame.control_word.token, protocol, pipe, dst_ia)
    load_param.send(protocol, pipe, dst_ia, frame_to_bytes(frame))


def block_send(protocol: int, pipe: int, dst_ia: int, frame: BlockFrame):
    """
    块传输发送数据
    """
    if frame is None:
        return

    load_param = get_load_param()
    if not load_param.is_allow_send(pipe):
        log.warn('block send failed!pipe:0x%x is not allow send.token:%d', pipe, frame.control_word.token)
        return
    log.info('block send frame.token:%d protocol:%d pipe:0x%x dst ia:0x%x offset:%d', frame.control_word.token,
             protocol, pipe, dst_ia, frame.block_header.offset)
    load_param.send(protocol, pipe, dst_ia, block_frame_to_bytes(frame))


def send_rst_frame(protocol: int, pipe: int, dst_ia: int, error_code: int, rid: int, token: int):
    """
    发送错误码
    """
    log.info('send rst frame:0x%x!token:%d protocol:%d pipe:0x%x dst ia:0x%x', error_code, token, protocol, pipe,
             dst_ia)
    frame = Frame()
    frame.control_word.code = CODE_RST
    frame.control_word.block_flag = 0
    frame.control_word.rid = rid
    frame.control_word.token = token
    frame.control_word.payload_len = 1
    frame.payload.append((error_code | 0x80) & 0xff)
    send(protocol, pipe, dst_ia, frame)
