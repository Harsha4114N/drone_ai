from setuptools import find_packages, setup

package_name = 'drone_ai'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='n_harsha',
    maintainer_email='n_harsha@todo.todo',
    description='AI-Powered Drone',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'yolo_detector = drone_ai.yolo_detector:main',
            'geolocation = drone_ai.geolocation:main',
	    'sim_cinematic_ai = drone_ai.sim_cinematic_ai:main',
	    'video_streamer = drone_ai.video_streamer:main',
        ],
    },
)
