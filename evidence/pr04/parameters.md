# PR04. Параметры patrol

Опыт выполнен в Ubuntu 26.04.1 LTS, ROS 2 Lyrical и Python 3.14.4.
Контейнер `ros2` запущен из образа
`tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`,
digest `sha256:23bbfbd0bac264da8ef39fb599b9d58b209b06603b49e979eba8021286c56b6e`.
Рабочая директория `/home/ubuntu/ros2_ws` подключена с macOS.
Для автоматического повтора симулятор запущен с `QT_QPA_PLATFORM=offscreen`
в отдельном ROS-домене 46. Команды для повторения через noVNC приведены в
[README](../../README.md#pr04-параметры-движения).

Ниже приведён фактический вывод команд в терминале Ubuntu. Для каждого
шестисекундного замера оставлено последнее доступное окно. Код 124 означает,
что команду остановил `timeout`. Результат `ros2 param set` проверялся
по сообщению CLI, чтению параметра и частоте потока.

## Воспроизведение с отключённой проверкой

В локальной ветке `codex/pr04-reproduce-zero` на коммите
`fa0028829ce3c86410e66e66a821aa7a1c3ff069` условие `if name not in PARAMETER_LIMITS:`
в валидаторе заменено на `if name == 'publish_hz' or name not in PARAMETER_LIMITS:`.
После перехода на 5 Гц попытка установить частоту в ноль дошла до
обработчик применения параметров. Вычисление `1.0 / publish_hz`
завершилось исключением. Нода остановилась до ответа на запрос, а следующий
замер не получил сообщений.

**Терминал Ubuntu — запуск и измерение с отключённой проверкой**

```text
$ source /opt/ros/lyrical/setup.bash
$ source install/setup.bash
$ export ROS_DOMAIN_ID=46
$ QT_QPA_PLATFORM=offscreen ros2 launch turtle_bringup sim.launch.py
$ ros2 topic type /turtle1/pose
turtlesim_msgs/msg/Pose
$ ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
$ timeout 10s ros2 param get /patrol publish_hz
Double value is: 10.0
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
average rate: 9.997
    min: 0.097s max: 0.103s std dev: 0.00141s window: 49
exit=124
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
average rate: 5.003
    min: 0.197s max: 0.203s std dev: 0.00213s window: 19
exit=124
$ timeout -s INT 10s ros2 param set /patrol publish_hz 0.0
exit=124
patrol exit=1
$ cat log/pr04/broken-patrol.txt
Traceback (most recent call last):
[промежуточные кадры опущены]
  File "/home/ubuntu/ros2_ws/build/patrol/patrol/patrol.py", line 81, in _apply_parameters
    timer = self.create_timer(1.0 / publish_hz, self._publish_command, autostart=False)
                              ~~~~^~~~~~~~~~~~
ZeroDivisionError: division by zero
[ros2run]: Process exited with failure 1
$ timeout -s INT 5s ros2 param get /patrol publish_hz
Node not found
exit=1
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
exit=124
```

## Повтор с проверкой

В исправной версии `da81b8b9a52fb15b21cc405227ab03b576515e25` допустимые 5 Гц
уменьшили измеренный поток с 9.999 до 5.001 Гц. Запрос с нулём отклонён,
`ros2 param get` показал 5.0, а поток составил 4.998 Гц.
Изменения `linear_speed` и `turn_rate` появились в полях
`linear.x` и `angular.z` следующей команды `Twist`.

**Терминал Ubuntu — повторная проверка параметров, сервиса и действия**

```text
$ source /opt/ros/lyrical/setup.bash
$ source install/setup.bash
$ export ROS_DOMAIN_ID=46
$ QT_QPA_PLATFORM=offscreen ros2 launch turtle_bringup sim.launch.py
$ ros2 topic type /turtle1/pose
turtlesim_msgs/msg/Pose
$ ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
$ timeout 10s ros2 param get /patrol publish_hz
Double value is: 10.0
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
average rate: 9.999
    min: 0.097s max: 0.103s std dev: 0.00138s window: 49
exit=124
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
average rate: 5.001
    min: 0.198s max: 0.202s std dev: 0.00100s window: 24
exit=124
$ timeout -s INT 10s ros2 param set /patrol publish_hz 0.0
Setting parameter failed: publish_hz must be a finite number in [1.0, 30.0]
exit=0
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ timeout -s INT 6s ros2 topic hz /turtle1/cmd_vel
average rate: 4.998
    min: 0.197s max: 0.203s std dev: 0.00134s window: 24
exit=124
$ ros2 param set /patrol linear_speed 0.8
Set parameter successful
$ ros2 param set /patrol turn_rate -0.4
Set parameter successful
$ timeout 10s ros2 topic echo /turtle1/cmd_vel --once
linear:
  x: 0.8
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: -0.4
---
$ ros2 service call /clear std_srvs/srv/Empty '{}'
waiting for service to become available...
requester: making request: std_srvs.srv.Empty_Request()

response:
std_srvs.srv.Empty_Response()

$ ros2 action list -t
/turtle1/rotate_absolute [turtlesim_msgs/action/RotateAbsolute]
```

Сервис `/clear` принимает запрос и возвращает один ответ после очистки поля.
Действие `/turtle1/rotate_absolute` принимает цель поворота, может сообщать
прогресс, поддерживает отмену и возвращает результат по завершении.
