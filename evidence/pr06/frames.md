# PR06. Дерево TF модели Ackermann

Корень дерева — `base_link`. У корпуса X направлена вперёд, Y влево, Z вверх.
У `camera_optical_frame` Z направлена вперёд, X вправо, Y вниз.
XYZ указаны в метрах в системе родителя, RPY — в радианах.
[REP-103](https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst)

| Родитель | Потомок | XYZ | RPY при нулевом положении | Сочленение и ось | Топик | Владелец |
| --- | --- | --- | --- | --- | --- | --- |
| `base_link` | `camera_link` | (0.28, 0, 0.38) | (0, 0, 0) | `fixed` | `/tf_static` | `robot_state_publisher` |
| `camera_link` | `camera_optical_frame` | (0, 0, 0) | (−π/2, 0, −π/2) | `fixed` | `/tf_static` | `robot_state_publisher` |
| `base_link` | `lidar_link` | (0.28, 0, 0.38) | (0, 0, 0) | `fixed` | `/tf_static` | `robot_state_publisher` |
| `base_link` | `imu_link` | (0.28, 0, 0.38) | (0, 0, 0) | `fixed` | `/tf_static` | `robot_state_publisher` |
| `base_link` | `front_left_knuckle` | (0.40, 0.31, 0) | (0, 0, 0) | `revolute`, +Z | `/tf` | `robot_state_publisher` |
| `base_link` | `front_right_knuckle` | (0.40, −0.31, 0) | (0, 0, 0) | `revolute`, +Z | `/tf` | `robot_state_publisher` |
| `front_left_knuckle` | `front_left_wheel` | (0, 0, 0) | (0, 0, 0) | `continuous`, +Y | `/tf` | `robot_state_publisher` |
| `front_right_knuckle` | `front_right_wheel` | (0, 0, 0) | (0, 0, 0) | `continuous`, +Y | `/tf` | `robot_state_publisher` |
| `base_link` | `rear_left_wheel` | (−0.40, 0.31, 0) | (0, 0, 0) | `continuous`, +Y | `/tf` | `robot_state_publisher` |
| `base_link` | `rear_right_wheel` | (−0.40, −0.31, 0) | (0, 0, 0) | `continuous`, +Y | `/tf` | `robot_state_publisher` |

База 0.80 м, колея 0.62 м, радиус колеса 0.12 м. Три датчика имеют общую
позицию крепления из SDF. Геометрия цилиндра повернута отдельно от фрейма
колеса, поэтому ось цилиндра совпадает с осью вращения Y.

Один экземпляр `robot_state_publisher` публикует все десять связей.
Фиксированные связи доступны сразу. Для шести подвижных связей
`robot_state_publisher` использует углы и метки времени из `/joint_states`.
Проверка через `view_frames` с нулевыми углами охватывает всё дерево.

В дефектной версии `camera_link` становится родителем `lidar_link` при том же
локальном смещении. Поскольку камера тоже смещена на (0.28, 0, 0.38) и
сохраняет оси корпуса, `tf2_echo base_link lidar_link` измеряет
(0.56, 0, 0.76). После исправления измерение снова даёт (0.28, 0, 0.38).
