"""Republish the simulator pose with best-effort reliability."""

from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from turtlesim_msgs.msg import Pose

from .node_runner import run_node


class PoseRelay(Node):
    """Forward each incoming Pose to the sensor topic."""

    def __init__(self) -> None:
        """Create the pose input and best-effort output."""
        super().__init__('pose_relay')
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self._sensor_publisher = self.create_publisher(Pose, 'sensor_pose', qos)
        self._pose_subscription = self.create_subscription(
            Pose, 'pose', self._sensor_publisher.publish, qos)


def main() -> None:
    """Run the relay until shutdown."""
    run_node(PoseRelay)
