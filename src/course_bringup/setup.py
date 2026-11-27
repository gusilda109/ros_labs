from setuptools import setup

package_name = 'course_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/patrol.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Максим Ерченко',
    maintainer_email='gusilda109@gmail.com',
    description='Launch the patrol simulation, QoS demonstration, and MCAP recorder.',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'pose_relay = course_bringup.pose_relay:main',
            'pose_subscriber = course_bringup.pose_subscriber:main',
        ],
    },
)
