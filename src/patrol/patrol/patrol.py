"""Run the patrol node."""

import signal

from geometry_msgs.msg import Twist
from rclpy import init, spin, try_shutdown
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim_msgs.msg import Pose


def command_for_pose(pose: Pose | None) -> Twist:
    """Return a stationary command until the first pose arrives."""
    command = Twist()
    if pose is not None:
        command.linear.x = 0.5
        command.angular.z = 0.3
    return command


class Patrol(Node):
    """Store the latest pose and publish a command at 10 Hz."""

    def __init__(self) -> None:
        """Create the pose subscription, command publisher, and timer."""
        super().__init__('patrol')
        self._pose: Pose | None = None
        self._pose_subscription = self.create_subscription(
            Pose, '/turtle1/pose', self._store_pose, 10)
        self._command_publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer = self.create_timer(0.1, self._publish_command)

    def _store_pose(self, pose: Pose) -> None:
        self._pose = pose

    def _publish_command(self) -> None:
        self._command_publisher.publish(command_for_pose(self._pose))


def main() -> None:
    """Start the node and process callbacks until interrupted."""
    # Let rclpy shut down the context on SIGINT, even if ros2 run forwards it twice.
    previous_handler = signal.signal(signal.SIGINT, lambda *_: None)
    try:
        init()
        node = Patrol()
        try:
            spin(node)
        except ExternalShutdownException:
            pass
        finally:
            node.destroy_node()
            try_shutdown()
    finally:
        signal.signal(signal.SIGINT, previous_handler)


if __name__ == '__main__':
    main()
