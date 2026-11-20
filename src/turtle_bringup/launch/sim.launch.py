"""Запуск симулятора turtlesim одной нодой (ПР02)."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Вернуть описание запуска: один процесс turtlesim_node."""
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            output='screen',
        ),
    ])
