"""Check command selection without starting a ROS node."""

from geometry_msgs.msg import Twist, Vector3
from patrol.patrol import command_for_pose
from turtlesim_msgs.msg import Pose


def test_command_without_pose() -> None:
    """Keep every axis at zero until a pose arrives."""
    assert command_for_pose(None) == Twist()


def test_command_with_pose() -> None:
    """Use the requested speeds and keep all other axes zero."""
    pose = Pose(x=5.5, y=5.5, theta=0.0)
    assert command_for_pose(pose) == Twist(
        linear=Vector3(x=0.5), angular=Vector3(z=0.3))
