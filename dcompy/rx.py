"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
接收模块
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.block_rx import *
from dcompy.rx_con import *
from dcompy.waitlist import *


def rx_load():
    """
    模块载入
    """
    block_rx_set_callback(_deal_recv)


def _deal_recv(protocol: int, pipe: int, src_ia: int, frame: Frame):
    log.info('receive data.token:%d code:%d src ia:0x%x', frame.control_word.token, frame.control_word.code, src_ia)
    if frame.control_word.code == CODE_CON or frame.control_word.code == CODE_NON:
        rx_con(protocol, pipe, src_ia, frame)
        return
    if frame.control_word.code == CODE_ACK:
        rx_ack_frame(protocol, pipe, src_ia, frame)
        return
    if frame.control_word.code == CODE_BACK:
        block_rx_back_frame(protocol, pipe, src_ia, frame)
        return
    if frame.control_word.code == CODE_RST:
        if not frame.payload or len(frame.payload) != 1 or frame.control_word.payload_len != 1:
            return
        rx_rst_frame(protocol, pipe, src_ia, frame)
        block_rx_deal_rst_frame(protocol, pipe, src_ia, frame)
        block_tx_deal_rst_frame(protocol, pipe, src_ia, frame)
        return


def receive(protocol: int, pipe: int, src_ia: int, data: bytearray):
    """
    接收数据.应用模块接收到数据后需调用本函数,本函数接收帧的格式为DCOM协议数据
    """
    frame, err = bytes_to_frame(data)
    if not err:
        log.warn('receive data error:bytes to frame failed.src ia:0x%x', src_ia)
        return

    if frame.control_word.block_flag == 0:
        _deal_recv(protocol, pipe, src_ia, frame)
    else:
        block_frame, err = bytes_to_block_frame(data)
        if not err:
            log.warn('receive data error:bytes to frame failed.src ia:0x%x', src_ia)
            return
        block_rx_receive(protocol, pipe, src_ia, block_frame)
