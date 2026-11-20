# PR02 — топики, типы и поля

ROS 2 Lyrical. Типы проверены командами `ros2 topic type` и `ros2 interface show`.

## Основные топики

| Топик | Тип | Кто публикует → кто подписан | Назначение |
|---|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | CLI (`ros2 topic pub`) или teleop → `/turtlesim` | команда скорости для черепахи |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | `/turtlesim` → CLI (`ros2 topic echo`) | текущее положение и скорость черепахи |

```
$ ros2 topic type /turtle1/pose
turtlesim_msgs/msg/Pose
```

В Lyrical тип позы — `turtlesim_msgs/msg/Pose` (в Jazzy было бы `turtlesim/msg/Pose`).

## `geometry_msgs/msg/Twist`

```
$ ros2 interface show geometry_msgs/msg/Twist
# This expresses velocity in free space broken into its linear and angular parts.

Vector3  linear
	float64 x
	float64 y
	float64 z
Vector3  angular
	float64 x
	float64 y
	float64 z
```

Twist — это два вектора `geometry_msgs/msg/Vector3` (поля `x`, `y`, `z`, тип `float64`):

| Поле | Смысл | Как использует turtlesim |
|---|---|---|
| `linear.x` | линейная скорость вперёд, ед./с | движение вперёд/назад по направлению взгляда |
| `linear.y` | линейная скорость вбок, ед./с | сдвиг вбок (в командах этой работы 0) |
| `linear.z` | линейная скорость вверх | не используется (плоский мир) |
| `angular.x` | угловая скорость вокруг оси X (крен) | не используется |
| `angular.y` | угловая скорость вокруг оси Y (тангаж) | не используется |
| `angular.z` | угловая скорость вокруг вертикальной оси (рыскание), рад/с | поворот: `> 0` против часовой стрелки |

Поля, не указанные в YAML команды (`'{linear: {x: 1.0}, angular: {z: 0.5}}'`), остаются равными 0.

## `turtlesim_msgs/msg/Pose`

```
$ ros2 interface show turtlesim_msgs/msg/Pose
float32 x
float32 y
float32 theta

float32 linear_velocity
float32 angular_velocity
```

| Поле | Тип | Смысл |
|---|---|---|
| `x` | `float32` | координата X в окне (0…≈11,09) |
| `y` | `float32` | координата Y |
| `theta` | `float32` | направление взгляда, рад (0 — вправо, растёт против часовой стрелки) |
| `linear_velocity` | `float32` | текущая линейная скорость |
| `angular_velocity` | `float32` | текущая угловая скорость |
