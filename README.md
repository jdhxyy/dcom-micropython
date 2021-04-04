# 海萤物联网教程：物联网RPC框架MicroPython DCOM
欢迎前往社区交流：[海萤物联网社区](http://www.ztziot.com)

## 简介
MicroPython是可以运行在微处理器上的Python解释器，它可以运行在一些单片机上，比如esp32，树莓派pico等。

因为不是全功能的Python，MicroPython做了很多裁剪，很多库与标准版的Python也不同。DCOM为了移植到MicroPython，做了一些适配工作。MicroPython版本的DCOM库所有API接口都和标准版本一致，使用方法也一致。

DCOM的简介与Python下的DCOM库可以查看文档：[海萤物联网教程：物联网RPC框架Python DCOM](https://blog.csdn.net/jdh99/article/details/115374729)

## 开源
- [github上的项目地址](https://github.com/jdhxyy/dcom-micropython)
- [gitee上的项目地址](https://gitee.com/jdhxyy/dcom-micropython)

## 安装
MicroPython版本的DCOM库已上传到pypi，包名是micropython-dcompy。可以通过pip下载到指定目录，比如以下命令是下载到package目录下：
```text
pip install --target=d:\package micropython-dcompy
```

下载后文件如下图：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210404110256562.png)

其中dcompy即是软件包，另外两个文件可以删除。


