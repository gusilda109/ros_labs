"""Run the patrol node."""

from collections.abc import Mapping
from math import isfinite
import signal

from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
from rclpy import init, spin, try_shutdown
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from turtlesim_msgs.msg import Pose


DEFAULT_LINEAR_SPEED = 0.5
DEFAULT_TURN_RATE = 0.3
DEFAULT_PUBLISH_HZ = 10.0
PARAMETER_LIMITS = {
    'linear_speed': (0.0, 1.0),
    'turn_rate': (-1.0, 1.0),
    'publish_hz': (1.0, 30.0),
}


def validate_parameters(values: Mapping[str, object]) -> str:
    """Return the reason for rejecting an update, or an empty string."""
    for name, value in values.items():
        if name not in PARAMETER_LIMITS:
            continue
        lower, upper = PARAMETER_LIMITS[name]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not lower <= value <= upper or not isfinite(value)):
            return f'{name} must be a finite number in [{lower}, {upper}]'
    return ''


def command_for_pose(
    pose: Pose | None,
    linear_speed: float = DEFAULT_LINEAR_SPEED,
    turn_rate: float = DEFAULT_TURN_RATE,
) -> Twist:
    """Return a stationary command until the first pose arrives."""
    command = Twist()
    if pose is not None:
        command.linear.x = linear_speed
        command.angular.z = turn_rate
    return command


class Patrol(Node):
    """Publish a command based on the latest pose and active parameters."""

    def __init__(self) -> None:
        """Create the pose subscription, command publisher, and timer."""
        super().__init__('patrol')
        self.add_on_set_parameters_callback(self._check_parameters)
        self.declare_parameters('', [
            ('linear_speed', DEFAULT_LINEAR_SPEED),
            ('turn_rate', DEFAULT_TURN_RATE),
            ('publish_hz', DEFAULT_PUBLISH_HZ),
        ])
        self._pose: Pose | None = None
        self._pose_subscription = self.create_subscription(
            Pose, '/turtle1/pose', self._store_pose, 10)
        self._command_publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self._publish_hz = self.get_parameter('publish_hz').get_parameter_value().double_value
        self._timer = self.create_timer(1.0 / self._publish_hz, self._publish_command)
        self.add_post_set_parameters_callback(self._apply_parameters)

    def _check_parameters(self, parameters: list[Parameter]) -> SetParametersResult:
        reason = validate_parameters({parameter.name: parameter.value for parameter in parameters})
        return SetParametersResult(successful=not reason, reason=reason)

    def _apply_parameters(self, parameters: list[Parameter]) -> None:
        if not any(parameter.name == 'publish_hz' for parameter in parameters):
            return
        publish_hz = self.get_parameter('publish_hz').get_parameter_value().double_value
        if publish_hz == self._publish_hz:
            return
        timer = self.create_timer(1.0 / publish_hz, self._publish_command, autostart=False)
        self._timer.cancel()
        self.destroy_timer(self._timer)
        self._timer = timer
        self._publish_hz = publish_hz
        timer.reset()

    def _store_pose(self, pose: Pose) -> None:
        self._pose = pose

    def _publish_command(self) -> None:
        linear_speed = self.get_parameter('linear_speed').get_parameter_value().double_value
        turn_rate = self.get_parameter('turn_rate').get_parameter_value().double_value
        self._command_publisher.publish(command_for_pose(self._pose, linear_speed, turn_rate))


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
