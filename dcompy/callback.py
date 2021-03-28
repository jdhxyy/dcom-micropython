"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
回调模块主文件
Authors: jdh99 <jdh821@163.com>
"""

import dcompy.log as log

from dcompy.system_error import *

_services = dict()


def register(protocol: int, rid: int, callback):
    """
    注册DCOM服务回调函数
    :param protocol: 协议号
    :param rid: 服务号
    :param callback: 回调函数.格式: func(pipe: int, src_ia: int, req: bytearray) (bytearray, int)
    :return: 返回值是应答和错误码.错误码为0表示回调成功,否则是错误码
    """
    log.info('register.protocol:%d rid:%d', protocol, rid)
    rid += protocol << 16
    _services[rid] = callback


def service_callback(protocol: int, pipe: int, src_ia: int, rid: int, req: bytearray) -> (bytearray, int):
    """
    回调资源号rid对应的函数
    """
    log.info('service callback.rid:%d', rid)
    rid += protocol << 16
    if rid not in _services:
        log.warn('service callback failed!can not find new rid:%d', rid)
        return None, SYSTEM_ERROR_INVALID_RID
    return _services[rid](pipe, src_ia, req)
