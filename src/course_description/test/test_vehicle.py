"""Check the expanded Ackermann model and its geometry contract."""

from math import isfinite, pi
from pathlib import Path
from xml.etree import ElementTree

import pytest
import xacro

MODEL = Path(__file__).resolve().parents[1] / 'urdf' / 'vehicle.urdf.xacro'
FIXED_PARENTS = {
    'camera_link': 'base_link',
    'camera_optical_frame': 'camera_link',
    'imu_link': 'base_link',
    'lidar_link': 'base_link',
}
WHEELS = ('front_left', 'front_right', 'rear_left', 'rear_right')


def expand(**overrides):
    """Return the expanded URDF for the given Xacro argument values."""
    return ElementTree.fromstring(
        xacro.process_file(str(MODEL), mappings=overrides).toxml()
    )


def vector(element, attribute):
    """Read a space-separated URDF vector."""
    return tuple(map(float, element.attrib[attribute].split()))


def test_lidar_parent():
    """Keep the lidar offset relative to the base."""
    joint = expand().find("joint[@name='lidar_joint']")
    assert joint.find('parent').attrib['link'] == 'base_link'
    assert joint.find('child').attrib['link'] == 'lidar_link'
    assert vector(joint.find('origin'), 'xyz') == pytest.approx((0.28, 0, 0.38))


def test_frame_tree():
    """Verify each expected edge and a single connected, acyclic tree."""
    robot = expand()
    expected = {child: (parent, 'fixed') for child, parent in FIXED_PARENTS.items()}
    for side in ('left', 'right'):
        knuckle = f'front_{side}_knuckle'
        expected[knuckle] = ('base_link', 'revolute')
        expected[f'front_{side}_wheel'] = (knuckle, 'continuous')
        expected[f'rear_{side}_wheel'] = ('base_link', 'continuous')
    joints = robot.findall('joint')
    edges = {
        joint.find('child').attrib['link']: (joint.find('parent').attrib['link'], joint.attrib['type'])
        for joint in joints
    }
    links = robot.findall('link')
    assert len(joints) == len(expected)
    assert len(links) == len(expected) + 1
    assert edges == expected
    assert {link.attrib['name'] for link in links} == {'base_link', *expected}


def test_sensor_poses():
    """Match the SDF mount and the REP-103 optical orientation."""
    robot = expand()
    for name in ('camera', 'imu', 'lidar'):
        origin = robot.find(f"joint[@name='{name}_joint']/origin")
        assert vector(origin, 'xyz') == pytest.approx((0.28, 0, 0.38))
        assert vector(origin, 'rpy') == pytest.approx((0, 0, 0))
    optical = robot.find("joint[@name='camera_optical_joint']/origin")
    assert vector(optical, 'xyz') == pytest.approx((0, 0, 0))
    assert vector(optical, 'rpy') == pytest.approx((-pi / 2, 0, -pi / 2))


@pytest.mark.parametrize(
    'overrides,wheelbase,track_width,radius',
    [
        ({}, 0.80, 0.62, 0.12),
        ({'wheelbase': '1.0', 'track_width': '0.70', 'wheel_radius': '0.14'}, 1.0, 0.70, 0.14),
    ],
)
def test_wheel_geometry(overrides, wheelbase, track_width, radius):
    """Check both default SDF dimensions and changed Xacro arguments."""
    robot = expand(**overrides)
    for name in WHEELS:
        axle, side = name.split('_')
        y = track_width / 2 if side == 'left' else -track_width / 2
        wheel_joint = robot.find(f"joint[@name='{name}_wheel_joint']")
        assert vector(wheel_joint.find('axis'), 'xyz') == (0, 1, 0)
        if axle == 'front':
            steering = robot.find(f"joint[@name='{name}_steering_joint']")
            assert vector(steering.find('origin'), 'xyz') == pytest.approx((wheelbase / 2, y, 0))
            assert vector(steering.find('axis'), 'xyz') == (0, 0, 1)
            expected_center = (0, 0, 0)
        else:
            expected_center = (-wheelbase / 2, y, 0)
        assert vector(wheel_joint.find('origin'), 'xyz') == pytest.approx(expected_center)

        link = robot.find(f"link[@name='{name}_wheel']")
        for kind in ('visual', 'collision'):
            geometry = link.find(kind)
            cylinder = geometry.find('geometry/cylinder')
            assert float(cylinder.attrib['radius']) == pytest.approx(radius)
            assert float(cylinder.attrib['length']) == pytest.approx(0.07)
            assert vector(geometry.find('origin'), 'rpy') == pytest.approx((pi / 2, 0, 0))


def test_body_geometry_and_inertia():
    """Check body dimensions and physically admissible diagonal inertia."""
    robot = expand()
    body = robot.find("link[@name='base_link']")
    for kind in ('visual', 'collision'):
        section = body.find(kind)
        assert vector(section.find('origin'), 'xyz') == pytest.approx((0, 0, 0.12))
        assert vector(section.find('geometry/box'), 'size') == pytest.approx((1.05, 0.52, 0.22))

    for inertial in robot.findall('link/inertial'):
        mass = float(inertial.find('mass').attrib['value'])
        assert isfinite(mass) and mass > 0
        inertia = inertial.find('inertia').attrib
        assert all(float(inertia[key]) == 0 for key in ('ixy', 'ixz', 'iyz'))
        a, b, c = sorted(float(inertia[key]) for key in ('ixx', 'iyy', 'izz'))
        assert all(isfinite(moment) for moment in (a, b, c))
        assert 0 < a
        assert c <= a + b
