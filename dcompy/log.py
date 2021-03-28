"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
日志模块
Authors: jdh99 <jdh821@163.com>
"""

import lagan

_TAG = "dcom"

_filter_level = lagan.LEVEL_WARN


def set_filter_level(level):
    """设置日志过滤级别"""
    global _filter_level
    _filter_level = level


def debug(msg: str, *args):
    """打印debug信息"""
    if _filter_level == lagan.LEVEL_OFF or lagan.LEVEL_DEBUG < _filter_level:
        return
    lagan.println(_TAG, lagan.LEVEL_DEBUG, msg, *args)


def info(msg: str, *args):
    """打印info信息"""
    if _filter_level == lagan.LEVEL_OFF or lagan.LEVEL_INFO < _filter_level:
        return
    lagan.println(_TAG, lagan.LEVEL_INFO, msg, *args)


def warn(msg: str, *args):
    """打印warn信息"""
    if _filter_level == lagan.LEVEL_OFF or lagan.LEVEL_WARN < _filter_level:
        return
    lagan.println(_TAG, lagan.LEVEL_WARN, msg, *args)


def error(msg: str, *args):
    """打印debug信息"""
    if _filter_level == lagan.LEVEL_OFF or lagan.LEVEL_ERROR < _filter_level:
        return
    lagan.println(_TAG, lagan.LEVEL_ERROR, msg, *args)
