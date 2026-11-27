"""Observe a Pose stream using the requested reliability policy."""

from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from turtlesim_msgs.msg import Pose

from .node_runner import run_node


class PoseSubscriber(Node):
    """Log receipt of the first sensor message."""

    def __init__(self) -> None:
        """Subscribe to the sensor topic using the configured reliability."""
        super().__init__('pose_subscriber')
        reliability = self.declare_parameter(
            'reliability', 'best_effort').get_parameter_value().string_value
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy[reliability.upper()])
        self._subscription = self.create_subscription(
            Pose, 'sensor_pose', self._log_pose, qos)
        self.get_logger().info(f'Waiting for {self._subscription.topic_name} ({reliability})')

    def _log_pose(self, pose: Pose) -> None:
        self.get_logger().info(
            f'Received pose: x={pose.x:.3f}, y={pose.y:.3f}, theta={pose.theta:.3f}',
            once=True,
        )


def main() -> None:
    """Run the subscriber until shutdown."""
    run_node(PoseSubscriber)
