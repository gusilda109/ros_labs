# Робототехника: лабораторные работы

## Среда
- Хост: macOS + Docker Desktop
- Образ: `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836` (Ubuntu, ROS 2 Lyrical)
- GUI: noVNC, http://127.0.0.1:6080/
- Рабочее пространство: `~/ros2_ws` на хосте = `/home/ubuntu/ros2_ws` в контейнере

Запуск контейнера (на хосте): `docker start ros2`

## Course kit
Ревизия v1-w11. Распаковывается в `.course-kit/v1/`, в git не хранится.
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
