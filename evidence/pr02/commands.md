# PR02 — команды и наблюдения

Среда: Docker-контейнер `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`, ROS 2 Lyrical, GUI через noVNC.
Корень репозитория = корень workspace: `/home/ubuntu/ros2_ws`. Домен: `ROS_DOMAIN_ID=16`.

## 1. Команды Linux

### `pwd`

```
$ cd "$(git rev-parse --show-toplevel)"
$ pwd
/home/ubuntu/ros2_ws
```

Назначение: показывает текущий каталог. `git rev-parse --show-toplevel` печатает корень репозитория, `cd "$(...)"` переходит туда, а `pwd` подтверждает, что я в корне workspace.

Результат: я в корне репозитория `/home/ubuntu/ros2_ws`, он же корень workspace.

Сравнение с установленным пакетом:

```
$ ros2 pkg prefix turtlesim
/opt/ros/lyrical
```

`pwd` — это мой рабочий каталог с исходниками, а `ros2 pkg prefix` — каталог, куда установлен пакет. Это разные места: turtlesim лежит в системной установке ROS, а не в моём репозитории.

### `source` и `printenv`

```
$ source /opt/ros/lyrical/setup.bash
$ export ROS_DOMAIN_ID=16
$ printenv ROS_DISTRO ROS_DOMAIN_ID
lyrical
16
```

Назначение: `source` выполняет `setup.bash` внутри текущей оболочки и задаёт переменные окружения (`PATH`, `AMENT_PREFIX_PATH`, `ROS_DISTRO` и др.). `printenv` печатает значения переменных и позволяет проверить, что окружение подключено.

Результат: `ROS_DISTRO=lyrical`, `ROS_DOMAIN_ID=16` — окружение ROS подключено, домен тот же, что в ПР01.

### `colcon build ... 2>&1 | tee`

```
$ set -o pipefail
$ colcon build --symlink-install --packages-select turtle_bringup \
    2>&1 | tee evidence/pr02/build.txt
Starting >>> turtle_bringup
Finished <<< turtle_bringup [0.56s]

Summary: 1 package finished [0.63s]
$ echo "exit=$?"
exit=0
```

Назначение: `2>&1` направляет stderr туда же, куда идёт stdout. `|` передаёт этот поток в `tee`, а `tee` показывает его на экране и одновременно записывает в файл. `set -o pipefail` нужен, чтобы при ошибке colcon весь конвейер вернул ненулевой код, хотя `tee` отработал успешно.

Результат: собран 1 пакет, без ошибок и предупреждений; лог в `evidence/pr02/build.txt`. `colcon test`: 5 тестов, 0 ошибок, 0 падений, 1 пропущен (`test_copyright`, генератор помечает его skip).

### `>` и `|`: в чём разница

- `>` перенаправляет stdout команды **в файл**. Файл создаётся или перезаписывается, на экран ничего не выводится. Пример: `ros2 topic info /cmd_vel --verbose > out.txt`.
- `|` передаёт stdout **на вход другой команде**. Файла нет, пока его не создаст следующая команда (например, `tee`). Пример: `colcon build 2>&1 | tee build.txt`.

### `source` и запуск новой программы: в чём разница

- `source setup.bash` выполняет скрипт **в текущей оболочке**. Переменные (`export ...`) остаются в этом терминале и наследуются всеми процессами, запущенными из него потом.
- `bash setup.bash` или `./setup.bash` запускают **новый процесс**. Он задаёт переменные у себя и завершается, а исходный терминал остаётся без изменений. Поэтому окружение ROS подключают через `source`.

## 2. Пустой пакет

```
$ cd src
$ ros2 pkg create --build-type ament_python --license Apache-2.0 \
    turtle_bringup --dependencies launch launch_ros turtlesim
$ cd ..
$ ls src/turtle_bringup
LICENSE
package.xml
resource
setup.cfg
setup.py
test
turtle_bringup
$ set -o pipefail
$ colcon build --symlink-install --packages-select turtle_bringup \
    2>&1 | tee evidence/pr02/build-empty.txt
```

В новом терминале:

```
$ source /opt/ros/lyrical/setup.bash
$ source install/setup.bash
$ ros2 pkg prefix turtle_bringup
/home/ubuntu/ros2_ws/install/turtle_bringup
$ ros2 node list --no-daemon --spin-time 2
(пусто)
```

Пакет найден в `install` моего workspace, но ни одной новой ноды не появилось: сборка и `source` только устанавливают файлы и задают переменные, они не запускают процессы.

## 3. Launch: запуск, проверка графа, остановка

Перед запуском остановил старые экземпляры turtlesim, если они были:

```
$ pkill -f turtlesim_node
```

Терминал A:

```
$ source /opt/ros/lyrical/setup.bash
$ source install/setup.bash
$ export ROS_DOMAIN_ID=16
$ ros2 pkg prefix turtle_bringup
/home/ubuntu/ros2_ws/install/turtle_bringup
$ ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
sim.launch.py
$ ros2 launch turtle_bringup sim.launch.py
[INFO] [launch]: All log files can be found below /home/ubuntu/.ros/log/2026-11-20-06-29-51-101200-e1ac9704e8b4-3516
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [turtlesim_node-1]: process started with pid [3528]
[turtlesim_node-1] [INFO] [1795156191.211117545] [turtlesim]: Starting turtlesim with node name /turtlesim
[turtlesim_node-1] [INFO] [1795156191.213624004] [turtlesim]: Spawning turtle [turtle1] at x=[5.544445], y=[5.544445], theta=[0.000000]
```

Открылось одно окно turtlesim.

Терминал C:

```
$ ros2 node list --no-daemon --spin-time 2
/turtlesim
```

Остановка: Ctrl+C в терминале A.

```
[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[turtlesim_node-1] [INFO] [1795156256.962136881] [rclcpp]: signal_handler(signum=2)
[INFO] [turtlesim_node-1]: process has finished cleanly [pid 3528]
```

После остановки `ros2 node list --no-daemon --spin-time 2` в C: пустой вывод. Launch при завершении остановил запущенный им turtlesim, окно закрылось.

Для опыта ниже launch запущен заново в A.

## 4. Команда → движение

В терминалах B и C: `source /opt/ros/lyrical/setup.bash`, `export ROS_DOMAIN_ID=16`. Teleop не запущен.

```
$ ros2 topic type /turtle1/pose
turtlesim_msgs/msg/Pose
$ ros2 topic echo /turtle1/pose --once
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
---
```

B:

```
$ ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
    '{linear: {x: 1.0}, angular: {z: 0.5}}'
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))
```

C:

```
$ ros2 topic echo /turtle1/pose --once
x: 6.509308815002441
y: 5.796990871429443
theta: 0.5040000081062317
linear_velocity: 0.0
angular_velocity: 0.0
---
```

Ожидание: `linear.x = 1.0` — вперёд по направлению взгляда, `angular.z = 0.5` — поворот против часовой стрелки. turtlesim выполняет команду около 1 с, затем останавливается, поэтому черепаха проедет короткую дугу влево: примерно на 1 единицу вперёд, `theta` увеличится примерно на 0,5 рад.

| | x | y | theta |
|---|---|---|---|
| До | 5.544 | 5.544 | 0.000 |
| После | 6.509 | 5.797 | 0.504 |

Вывод: направление совпало с ожиданием. Черепаха сместилась на ≈0,96 по x и ≈0,25 по y (дуга влево), theta выросла на ≈0,5 рад, после чего черепаха остановилась (`linear_velocity: 0.0`): одна публикация даёт движение примерно на 1 с.

## 5. Ошибка в имени топика и исправление

### Сбой: публикация в `/cmd_vel`

B:

```
$ ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
    /cmd_vel geometry_msgs/msg/Twist \
    '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Черепаха: стоит на месте всё время, пока идёт публикация.

C, пока издатель работает:

```
$ ros2 topic info /cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 1

Node name: _ros2cli_4026
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: PUBLISHER
GID: 01.0f.eb.7d.ba.0f.95.4c.00.00.00.00.00.00.07.03
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (10)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 0

$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 0

Subscription count: 1

Node name: turtlesim
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: SUBSCRIPTION
GID: 01.0f.eb.7d.71.0e.a4.21.00.00.00.00.00.00.1c.04
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (7)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite
```

Издатель остановлен через Ctrl+C.

### Исправление: только имя топика

B (скорость, тип и домен те же):

```
$ ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
    /turtle1/cmd_vel geometry_msgs/msg/Twist \
    '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Черепаха: сразу поехала по кругу против часовой стрелки.

C:

```
$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 1

Node name: _ros2cli_4105
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: PUBLISHER
GID: 01.0f.eb.7d.09.10.51.31.00.00.00.00.00.00.07.03
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (10)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 1

Node name: turtlesim
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: SUBSCRIPTION
GID: 01.0f.eb.7d.71.0e.a4.21.00.00.00.00.00.00.1c.04
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (7)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite
```

Издатель остановлен через Ctrl+C, черепаха остановилась примерно через 1 с.

### Сравнение «до / сбой / после»

| Стадия | Топик издателя | Издатели в топике | Подписчики в топике | Движение |
|---|---|---|---|---|
| До | `/turtle1/cmd_vel` (`--once`) | 1 (CLI, одно сообщение) | 1 (`/turtlesim`) | короткая дуга, затем остановка |
| Сбой | `/cmd_vel` | 1 (`_ros2cli_…`) | 0 | нет |
| После | `/turtle1/cmd_vel` | 1 (`_ros2cli_4105`) | 1 (`turtlesim`) | по кругу; после Ctrl+C остановка ≈ через 1 с |

### Почему правильного типа недостаточно

ROS связывает издателя и подписчика по **полному имени топика**, и только потом сверяет тип и QoS. Издатель `/cmd_vel` был виден в графе (обнаружение работает: CLI видит его тип и количество конечных точек), но в топике `/cmd_vel` нет ни одного подписчика. turtlesim подписан на `/turtle1/cmd_vel`, а это другой топик, несмотря на тот же тип `geometry_msgs/msg/Twist`. Сообщения уходили, но не доставлялись никому.

- **Обнаружение (discovery):** участники одного домена узнают друг о друге: ноды, топики, типы. В сбое это работало — оба топика видны.
- **Доставка:** сообщение получает только подписчик с тем же именем топика, совместимым типом и QoS. В сбое пары издатель–подписчик не было, поэтому доставки не было.

Исправлено только имя `/cmd_vel` → `/turtle1/cmd_vel`. Тип, скорость и домен не менялись, и после этого черепаха снова поехала. Значит, причиной было именно имя.
