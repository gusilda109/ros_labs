"""Launch one simulator, a namespaced patrol, and optional MCAP recording."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    """Configure topic remaps, reliability, and the recorder command."""
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    reliability = LaunchConfiguration('subscriber_reliability')
    sensor_topic = PathJoinSubstitution(['/', namespace, 'sensor_pose'])

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace', default_value='robot_a', description='Namespace for the patrol system'),
        DeclareLaunchArgument(
            'record', default_value='false', choices=['true', 'false'],
            description='Start the MCAP recorder'),
        DeclareLaunchArgument(
            'bag_dir', default_value='pr05_bag', description='New bag output directory'),
        DeclareLaunchArgument(
            'subscriber_reliability',
            default_value='best_effort',
            choices=['reliable', 'best_effort'],
            description='Reliability requested by the sensor subscriber',
        ),
        LogInfo(msg=['Sensor topic: ', sensor_topic, '; subscriber: ', reliability]),
        LogInfo(msg=['Recording MCAP to ', bag_dir], condition=IfCondition(record)),
        Node(package='turtlesim', executable='turtlesim_node', output='screen'),
        Node(
            package='patrol',
            executable='patrol',
            namespace=namespace,
            remappings=[
                ('turtle1/pose', '/turtle1/pose'),
                ('cmd_vel', '/turtle1/cmd_vel'),
            ],
            output='screen',
        ),
        Node(
            package='course_bringup',
            executable='pose_relay',
            namespace=namespace,
            remappings=[('pose', '/turtle1/pose')],
            output='screen',
        ),
        Node(
            package='course_bringup',
            executable='pose_subscriber',
            namespace=namespace,
            parameters=[{'reliability': reliability}],
            output='screen',
        ),
        ExecuteProcess(
            cmd=['ros2', 'bag', 'record', '-s', 'mcap', '-o', bag_dir, '--topics', sensor_topic],
            name='record_sensor_pose',
            condition=IfCondition(record),
            output='screen',
        ),
    ])
