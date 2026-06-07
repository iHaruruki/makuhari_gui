import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'makuhari_gui'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name),glob('launch/*launch.[pxy][yma]*')),
        (os.path.join('share', package_name, 'rviz'),glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Haruki Isono',
    maintainer_email='haruki.isono861@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'navigation_mode_display_node = makuhari_gui.navigation_mode_display:main',
        ],
    },
)
