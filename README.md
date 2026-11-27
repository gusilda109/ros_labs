# Робототехника: лабораторные работы

## Среда
- Хост: macOS + Docker Desktop
- Образ: `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836` (Ubuntu, ROS 2 Lyrical)
- GUI: noVNC, http://127.0.0.1:6080/
- Рабочее пространство: `~/ros2_ws` на хосте = `/home/ubuntu/ros2_ws` в контейнере

Запуск контейнера (на хосте): `docker start ros2`

## Course kit
Ревизия v1-w12. Распаковывается в `.course-kit/v1/`, в git не хранится.
CI скачивает зафиксированную ревизию и проверяет SHA-256.

## PR01: граф turtlesim и разрыв доменов

Во всех терминалах контейнера:

    source /opt/ros/lyrical/setup.bash
    export ROS_DOMAIN_ID=16

Терминал A: `ros2 run turtlesim turtlesim_node`
Терминал B: `ros2 run turtlesim turtle_teleop_key`
Терминал C: наблюдение за графом:

    ros2 node list --no-daemon --spin-time 2
    ros2 topic list -t
    ros2 node info /turtlesim
    POSE_TYPE=$(ros2 topic type /turtle1/pose)
    ros2 topic echo /turtle1/pose --once
    ros2 topic hz /turtle1/pose

Разрыв: teleop в B и CLI в C перезапускаются с `ROS_DOMAIN_ID=17`, а симулятор остаётся в 16:

    timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once   # ожидается exit=124

Восстановление: B и C снова в домене 16, тот же тест даёт exit=0.

Результаты лежат в `evidence/pr01/`. Проверка:

    python3 -m json.tool evidence/pr01/environment.json > /dev/null
    python3 .course-kit/v1/tools/check_practice.py PR01 --submission .

## PR02: пакет turtle_bringup и launch-файл

Пакет `src/turtle_bringup` (ament_python) устанавливает `launch/sim.launch.py`, который запускает `turtlesim_node`.
Корень репозитория — корень workspace.

Сборка (терминал контейнера, корень репозитория):

    source /opt/ros/lyrical/setup.bash
    set -o pipefail
    colcon build --symlink-install --packages-select turtle_bringup \
      2>&1 | tee evidence/pr02/build.txt

Запуск (новый терминал):

    source /opt/ros/lyrical/setup.bash
    source install/setup.bash
    export ROS_DOMAIN_ID=16
    ros2 launch turtle_bringup sim.launch.py

Команда движения (другой терминал, тот же домен):

    ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
      '{linear: {x: 1.0}, angular: {z: 0.5}}'

Сбой для опыта: та же команда в `/cmd_vel` — издатель виден, подписчика нет:

    ros2 topic pub --rate 1 --wait-matching-subscriptions 0 /cmd_vel geometry_msgs/msg/Twist \
      '{linear: {x: 1.0}, angular: {z: 0.5}}'
    ros2 topic info /cmd_vel --verbose
    ros2 topic info /turtle1/cmd_vel --verbose

CI (`ros-build`) в контейнере `ros:lyrical-ros-base` собирает пакет, проверяет, что `sim.launch.py`
установлен в `install/turtle_bringup/share/turtle_bringup/launch`, разбирает его через
`ros2 launch ... --show-args` (без GUI) и запускает `colcon test`.

Результаты лежат в `evidence/pr02/`. Проверка:

    python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
    python3 .course-kit/v1/tools/check_practice.py PR02 --submission .

## PR04. Параметры движения

В терминале macOS запустите контейнер командой `docker start ros2`
и откройте в браузере [рабочий стол Ubuntu](http://localhost:6080/).
Во всех терминалах Ubuntu для этого опыта используется отдельный домен 46.

**Терминал Ubuntu A — сборка и симулятор**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
export ROS_DOMAIN_ID=46
ros2 launch turtle_bringup sim.launch.py
```

**Терминал Ubuntu B — нода `patrol`**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=46
ros2 topic type /turtle1/pose
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

**Терминал Ubuntu C — параметры и проверка**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=46
ros2 param get /patrol publish_hz
timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
ros2 param set /patrol publish_hz 5.0
timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
ros2 param set /patrol publish_hz 0.0
ros2 param get /patrol publish_hz
timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
ros2 service call /clear std_srvs/srv/Empty '{}'
ros2 action list -t
python3 -m pytest src/patrol/test
python3 .course-kit/v1/tools/check_practice.py PR04 --submission .
```

Пределы параметров включительные. `linear_speed` принимает 0–1 м/с,
`turn_rate` — от −1 до 1 рад/с, `publish_hz` — 1–30 Гц.
После отклонения нуля параметр и поток остаются на 5 Гц. Команда `timeout`
завершает каждый замер через 6 секунд. Результаты обоих запусков сохранены
в [evidence/pr04/parameters.md](evidence/pr04/parameters.md).

## PR05. Общий запуск, QoS и MCAP

В терминале macOS запустите контейнер командой `docker start ros2`.
На macOS откройте [рабочий стол Ubuntu](http://localhost:6080/). В обоих
терминалах Ubuntu для опыта выбран домен 57.

**Терминал Ubuntu A — сборка и живой запуск**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install
source install/setup.bash
export ROS_DOMAIN_ID=57
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=reliable record:=false
```

**Терминал Ubuntu B — проверка несовместимости**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=57
ros2 node list
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic info /robot_a/sensor_pose --verbose
timeout -k 2s -s INT 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once
echo "$?"
```

Код `124` означает тайм-аут. Если ROS CLI не завершится в течение двух
секунд после SIGINT, `timeout` принудительно остановит его с кодом `137`. В терминале A нажмите Ctrl+C и запустите систему
с `best_effort`. Для нового опыта используйте новый путь записи.

**Терминал Ubuntu A — совместимый подписчик и запись**

```bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=best_effort record:=true \
  bag_dir:=log/pr05-bag
```

**Терминал Ubuntu B — проверка живого потока**

```bash
timeout -k 2s -s INT 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once
echo "$?"
```

Код `0` означает получение сообщения. Дайте записи поработать ещё минимум
10 секунд, затем нажмите Ctrl+C в A и дождитесь завершения всех процессов.

**Терминал Ubuntu A — воспроизведение записанного потока**

```bash
ros2 bag play log/pr05-bag --qos-profile-overrides-path config/qos-overrides.yaml
```

**Терминал Ubuntu B — проверка обоих профилей на воспроизведении**

```bash
timeout -k 2s -s INT 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once
echo "$?"
timeout -k 2s -s INT 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once
echo "$?"
ros2 bag info log/pr05-bag
```

Ожидаемые коды при воспроизведении — `124` и `0`. Готовый MCAP и
вывод проверок лежат в [evidence/pr05](evidence/pr05).

## PR06. Модель Ackermann и статические преобразования

В пакете `course_description` параметры `wheelbase`, `track_width` и `wheel_radius`
задают колёсную базу, колею и радиус колеса в метрах. Значения по умолчанию
взяты из `models/course_ackermann/model.sdf` в course kit.

**Браузер на macOS.** Откройте [рабочий стол Ubuntu](http://localhost:6080/).

**Терминал Ubuntu A — сборка и RViz**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install --packages-select course_description
source install/setup.bash
export ROS_DOMAIN_ID=66
ros2 launch course_description vehicle.launch.py
```

В RViz уже выбран Fixed Frame `base_link`. Корпус и фиксированные фреймы
доступны сразу. Для отображения колёс нужен поток `/joint_states`.
Для запуска без RViz добавьте `rviz:=false`.

**Терминал Ubuntu B — модель, тесты и TF**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=66
xacro src/course_description/urdf/vehicle.urdf.xacro > /tmp/vehicle.urdf
check_urdf /tmp/vehicle.urdf
colcon test --packages-select course_description
colcon test-result --test-result-base build/course_description --verbose
timeout -k 2s -s INT 5s ros2 run tf2_ros tf2_echo base_link lidar_link
(cd /tmp && ros2 run tf2_tools view_frames)
ros2 topic info /tf_static --verbose --no-daemon --spin-time 2
timeout -k 2s -s INT 4s ros2 topic echo /tf_static --once --qos-durability transient_local --qos-reliability reliable
timeout -k 2s -s INT 4s ros2 topic echo /tf_static --once --qos-durability volatile --qos-reliability reliable
```

`tf2_echo` работает непрерывно, поэтому команда с `timeout` останавливает его
после нескольких измерений. В опыте с `/tf_static` поздний подписчик
`transient_local` получает сохранённое сообщение и завершается с кодом 0.
Подписчик `volatile` в тех же условиях завершается по тайм-ауту с кодом 124.

**Терминал Ubuntu C — положения колёс для RViz и полного дерева TF**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=66
ros2 topic pub -r 10 /joint_states sensor_msgs/msg/JointState \
  '{header: auto, name: [front_left_steering_joint, front_right_steering_joint, front_left_wheel_joint, front_right_wheel_joint, rear_left_wheel_joint, rear_right_wheel_joint], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}'
```

Оставьте этот терминал работающим, пока повторяете `view_frames` в терминале B.

[Контракт фреймов](evidence/pr06/frames.md) ·
[Проверки модели и дефекта](evidence/pr06/model-check.txt) ·
[Опыт с QoS](evidence/pr06/tf-qos.txt)
