import sys

from setuptools import setup

if not (sys.version_info[0] == 3):
    sys.exit("Link IoT Edge only support Python 3")

setup(
    name='iotedge_driver_link_sdk',
    version='0.2.0',
    author='ucloud.cn',
    url='https://pypi.org/project/iotedge_driver_link_sdk/',
    author_email='joy.zhou@ucloud.cn',
    packages=['iotedgedriverlinksdk'],
    platforms="any",
    license='Apache 2 License',
    install_requires=[
        "asyncio-nats-client>=0.10.0",
        "cachetools>=4.0.0"
    ],
    description="IoT Edge Driver Link SDK",
    long_description="UIoT Edge Driver Link SDK\n https://www.ucloud.cn/site/product/uiot.html"
)
