"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
Device Communication Protocol(DCOM)：设备间通信协议。 DCOM协议可用于物联网设备之间RPC通信。
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.rx import *
from dcompy.common import *

import _thread
import uasyncio as asyncio


def load(param: LoadParam):
    set_load_param(param)
    rx_load()
    _thread.start_new_thread(_main_thread, ())


def _main_thread():
    loop = asyncio.new_event_loop()
    loop.create_task(block_rx_run())
    loop.create_task(block_tx_run())
    loop.create_task(waitlist_run())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    loop.close()
