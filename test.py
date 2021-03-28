import dcompy
import lagan


def main():
    case1()


def case1():
    lagan.load(0)
    lagan.set_filter_level(lagan.LEVEL_DEBUG)
    dcompy.set_filter_level(lagan.LEVEL_DEBUG)

    load()
    req, error = dcompy.call(0, 0, 0x1234, 1, 10000, bytearray([1, 2, 3]))
    print('0x%x' % error)
    print_hex(req)


def load():
    param = dcompy.LoadParam()
    param.block_retry_max_num = 5
    param.block_retry_interval = 1000
    param.is_allow_send = is_allow_send
    param.send = send
    dcompy.load(param)


def is_allow_send(port: int) -> bool:
    return True


def send(protocol: int, port: int, dst_ia: int, data: bytearray):
    print("protocol:%d dst_ia:%x, port:%d send:" % (protocol, dst_ia, port))
    print_hex(data)


def print_hex(data: bytearray):
    for i in data:
        print("%02x" % i, end=' ')
    print()


def case2():
    load()
    dcompy.call_async(1, 0, 0x1234, 1, 3000, bytearray([1, 2, 3]), deal_resp)


def deal_resp(req: bytearray, error: int):
    print('0x%x' % error)
    print_hex(req)


def case3():
    load()
    req, error = dcompy.call(0, 0, 0x1234, 1, 0, bytearray([1, 2, 3]))
    print('0x%x' % error)
    print_hex(req)


def case4():
    load()
    dcompy.call_async(2, 0, 0x1234, 1, 1000, bytearray([1, 2, 3]), deal_resp)


def case5():
    load()
    arr = bytearray()
    for i in range(501):
        arr.append(i & 0xff)
    req, error = dcompy.call(1, 0, 0x1234, 1, 0, arr)
    print('error:0x%x' % error)
    print_hex(req)


def case6():
    lagan.load(0)
    lagan.set_filter_level(lagan.LEVEL_DEBUG)
    dcompy.set_filter_level(lagan.LEVEL_DEBUG)

    load()
    arr = bytearray()
    for i in range(501):
        arr.append(i & 0xff)
    req, error = dcompy.call(1, 0, 0x1234, 1, 3000, arr)
    print('error:0x%x' % error)
    print_hex(req)


if __name__ == '__main__':
    main()
