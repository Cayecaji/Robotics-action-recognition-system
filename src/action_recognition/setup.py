import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'action_recognition'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.yaml'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cayecaji',
    maintainer_email='cayetanocaji@gmail.com',
    description='Package designed for human action recognition for exhanced human robot interaction',
    license='Apache License 2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'tracking_node = action_recognition.tracking_node:main',
            'action_recognition_core = action_recognition.action_recognition_core:main',
            'hri_node = action_recognition.hri_node:main'
        ],
    },
)
