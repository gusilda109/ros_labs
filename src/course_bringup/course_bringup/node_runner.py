"""Run the demonstration nodes with interruptible executor waits."""

from collections.abc import Callable

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions


def run_node(create_node: Callable[[], Node]) -> None:
    """Run callbacks until Ctrl+C and then shut down the ROS context."""
    with rclpy.init(signal_handler_options=SignalHandlerOptions.NO):
        node = create_node()
        try:
            with SingleThreadedExecutor() as executor:
                executor.add_node(node)
                while rclpy.ok():
                    # Return to Python periodically even when no messages match.
                    executor.spin_once(timeout_sec=0.5)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
