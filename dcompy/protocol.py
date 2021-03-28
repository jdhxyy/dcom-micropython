"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
dcom协议
Authors: jdh99 <jdh821@163.com>
"""

# CODE码
CODE_CON = 0
CODE_NON = 1
CODE_ACK = 2
CODE_RST = 3
CODE_BACK = 4

# 单帧最大字节数.超过此字节数需要块传输
SINGLE_FRAME_SIZE_MAX = 255

# 控制字字节数
CONTROL_WORD_LEN = 4
# 块传输头部长度
BLOCK_HEADER_LEN = 6


# ControlWord 控制字
class ControlWord:
    payload_len = 0
    token = 0
    rid = 0
    block_flag = 0
    code = 0


# Frame dcom帧
class Frame:
    def __init__(self):
        self.control_word = ControlWord()
        self.payload = bytearray()


# BlockHeader 块传输头部
class BlockHeader:
    crc16 = 0
    total = 0
    offset = 0


# BlockFrame 块传输帧.重定义了dcom帧的载荷
# 此时控制字中的载荷长度为本帧长度.块传输中的总字节数指示了整个块的字节数
class BlockFrame:
    def __init__(self):
        self.control_word = ControlWord()
        self.block_header = BlockHeader()
        self.payload = bytearray()
