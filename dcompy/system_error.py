"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
错误码
Authors: jdh99 <jdh821@163.com>
"""

# 系统错误码
# 正确值
SYSTEM_OK = 0
# 接收超时
SYSTEM_ERROR_RX_TIMEOUT = 0x10
# 发送超时
SYSTEM_ERROR_TX_TIMEOUT = 0x11
# 内存不足
SYSTEM_ERROR_NOT_ENOUGH_MEMORY = 0x12
# 没有对应的资源ID
SYSTEM_ERROR_INVALID_RID = 0x13
# 块传输校验错误
SYSTEM_ERROR_WRONG_BLOCK_CHECK = 0x14
# 块传输偏移地址错误
SYSTEM_ERROR_WRONG_BLOCK_OFFSET = 0x15
# 参数错误
SYSTEM_ERROR_PARAM_INVALID = 0x16
