"""Check parameter validation without starting a ROS node."""

from patrol.patrol import validate_parameters
import pytest


def test_publish_hz_change() -> None:
    """Accept both the default frequency and a change to 5 Hz."""
    assert validate_parameters({'publish_hz': 10.0}) == ''
    assert validate_parameters({'publish_hz': 5.0}) == ''


@pytest.mark.parametrize('value', [0.0, -5.0, float('nan'), float('inf'), 30.1])
def test_invalid_publish_hz(value: float) -> None:
    """Reject invalid frequencies before computing the timer period."""
    assert validate_parameters({'publish_hz': value}).startswith('publish_hz')


@pytest.mark.parametrize('values', [
    {'linear_speed': 0.0, 'turn_rate': -1.0, 'publish_hz': 1.0},
    {'linear_speed': 1.0, 'turn_rate': 1.0, 'publish_hz': 30.0},
])
def test_parameter_limits(values: dict[str, float]) -> None:
    """Accept both ends of each allowed range."""
    assert validate_parameters(values) == ''


@pytest.mark.parametrize(('name', 'value'), [
    ('linear_speed', -0.1), ('linear_speed', 1.1), ('linear_speed', float('nan')),
    ('turn_rate', -1.1), ('turn_rate', 1.1), ('turn_rate', float('-inf')),
])
def test_invalid_speeds(name: str, value: float) -> None:
    """Reject speeds outside the allowed finite ranges."""
    assert validate_parameters({name: value}).startswith(name)
