"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
接收到连接时处理
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.callback import *
from dcompy.block_tx import *


def rx_con(protocol: int, pipe: int, src_ia: int, frame: Frame):
    """
    接收到连接帧时处理函数
    """
    log.info('rx con.token:%d', frame.control_word.token)
    resp, err = service_callback(protocol, pipe, src_ia, frame.control_word.rid, frame.payload)

    # NON不需要应答
    if frame.control_word.code == CODE_NON:
        return

    if err != SYSTEM_OK:
        log.info('service send err:0x%x token:%d', err, frame.control_word.token)
        send_rst_frame(protocol, pipe, src_ia, err, frame.control_word.rid, frame.control_word.token)
        return

    if resp and len(resp) > SINGLE_FRAME_SIZE_MAX:
        # 长度过长启动块传输
        log.info('service send too long:%d.start block tx.token:%d', len(resp), frame.control_word.token)
        block_tx(protocol, pipe, src_ia, CODE_ACK, frame.control_word.rid, frame.control_word.token, resp)
        return

    ack_frame = Frame()
    ack_frame.control_word.code = CODE_ACK
    ack_frame.control_word.block_flag = 0
    ack_frame.control_word.rid = frame.control_word.rid
    ack_frame.control_word.token = frame.control_word.token
    if resp:
        ack_frame.control_word.payload_len = len(resp)
        ack_frame.payload.extend(resp)
    else:
        ack_frame.control_word.payload_len = 0
    send(protocol, pipe, src_ia, ack_frame)
