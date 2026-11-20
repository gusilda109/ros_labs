# PR01 — граф turtlesim

Среда: Docker-контейнер `tiryoh/ros2-desktop-vnc:lyrical-20260906T0836`, ROS 2 Lyrical, GUI через noVNC.
Рабочий домен: `ROS_DOMAIN_ID=16`, домен для разрыва: `17`.

## 1. Исправный граф

Запуск (все терминалы: `source /opt/ros/lyrical/setup.bash`, `export ROS_DOMAIN_ID=16`):

- терминал A: `ros2 run turtlesim turtlesim_node`
- терминал B: `ros2 run turtlesim turtle_teleop_key` — стрелки двигают черепаху
- терминал C: команды наблюдения ниже

### Ноды

```
$ ros2 node list --no-daemon --spin-time 2
/teleop_turtle
/turtlesim
```

| Нода | Роль |
|------|------|
| `/turtlesim` | симулятор: подписан на `/turtle1/cmd_vel`, публикует положение `/turtle1/pose` и цвет под черепахой `/turtle1/color_sensor`, предоставляет сервисы (`/spawn`, `/kill`, `/reset`, `/clear`, `/turtle1/set_pen`, телепортация) и action `/turtle1/rotate_absolute` |
| `/teleop_turtle` | управление с клавиатуры: читает стрелки и публикует команды скорости в `/turtle1/cmd_vel` |

### Топики и типы

```
$ ros2 topic list -t
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim_msgs/msg/Color]
/turtle1/pose [turtlesim_msgs/msg/Pose]
```

| Топик | Тип | Издатель → подписчик |
|-------|-----|----------------------|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | `/teleop_turtle` → `/turtlesim` |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | `/turtlesim` → (CLI-подписчик при проверке) |
| `/turtle1/color_sensor` | `turtlesim_msgs/msg/Color` | `/turtlesim` |
| `/rosout` | `rcl_interfaces/msg/Log` | служебный, логи всех нод |
| `/parameter_events` | `rcl_interfaces/msg/ParameterEvent` | служебный, изменения параметров |

Тип позы в Lyrical — `turtlesim_msgs/msg/Pose` (в Jazzy был бы `turtlesim/msg/Pose`):

```
$ ros2 topic type /turtle1/pose
turtlesim_msgs/msg/Pose
```

Фрагмент `ros2 node info /turtlesim` (топики; список сервисов опущен):

```
/turtlesim
  Subscribers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /turtle1/cmd_vel: geometry_msgs/msg/Twist
  Publishers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /rosout: rcl_interfaces/msg/Log
    /turtle1/color_sensor: turtlesim_msgs/msg/Color
    /turtle1/pose: turtlesim_msgs/msg/Pose
```

### Одно сообщение позы

```
$ ros2 topic echo /turtle1/pose --once
x: 5.544444561004639
y: 5.544444561004639
theta: 1.5631853342056274
linear_velocity: 0.0
angular_velocity: 0.0
---
```

Черепаха неподвижна, но поза всё равно публикуется.

### Частота `/turtle1/pose`

```
$ ros2 topic hz /turtle1/pose
...
average rate: 62.497
	min: 0.000s max: 0.034s std dev: 0.00198s window: 4890
```

- Средняя частота: **≈ 62,5 Гц** (с первых секунд держалась в диапазоне 62,30–62,50 Гц).
- Длительность замера: **≈ 78 с** (4890 сообщений / 62,5 Гц), остановлен вручную через Ctrl+C.
- Совпадает с ориентиром 60–62,5 Гц (таймер turtlesim 16 мс). Разброс интервалов небольшой (std dev ≈ 2 мс), редкие выбросы до 34 мс, скорее всего, вызваны нагрузкой VNC в Docker без GPU.

## 2. Разрыв и восстановление связи

Симулятор (терминал A) всё время работает в домене 16. Меняется только домен teleop (терминал B) и CLI-подписчика (терминал C); каждый раз оба процесса запускаются заново.

Тест в обеих стадиях одинаковый, отличаются только домен и имя файла:

    timeout -s INT -k 3s 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-<stage>.txt 2>&1
    printf '...: exit=%s\n' "$?"

Тип передаётся явно (`POSE_TYPE=turtlesim_msgs/msg/Pose`, получен на шаге 1): в чужом домене нет издателя, и CLI не может узнать тип сам.

**Отличие от команды из условия.** Вариант `timeout 5s ...` в моей среде зависал: `timeout` посылает SIGTERM, а `ros2 topic echo` на него не завершался, и процесс пришлось останавливать вручную (`pkill`). Поэтому использован `-s INT`: через 5 с приходит тот же сигнал, что и от Ctrl+C. `-k 3s` добивает процесс, если он не вышел. Код 124 по-прежнему означает истечение таймаута.

### Сбой (teleop и CLI в домене 17)

    export ROS_DOMAIN_ID=17
    ros2 node list --no-daemon --spin-time 2
    /teleop_turtle

- `/turtlesim` не виден, стрелки черепахой не управляют.
- `pose-broken.txt` пустой: за 5 с не пришло ни одного сообщения.
- `exit=124` — истёк таймаут.

### Восстановление (teleop и CLI снова в домене 16)

    export ROS_DOMAIN_ID=16
    ros2 node list --no-daemon --spin-time 2
    /teleop_turtle
    /turtlesim

- Стрелки снова двигают черепаху.
- `pose-fixed.txt` содержит позу:

      x: 5.544444561004639
      y: 5.544444561004639
      theta: -0.9279999732971191
      linear_velocity: 0.0
      angular_velocity: 0.0

- `exit=0`.

Коды возврата сохранены в `exit-codes.txt`.

### Сравнение

| Стадия | Домен turtlesim | Домен teleop | Домен CLI | `node list` | Поза | exit |
|--------|-----------------|--------------|-----------|-------------|------|------|
| До | 16 | 16 | 16 | `/teleop_turtle`, `/turtlesim` | приходит, ≈ 62,5 Гц | — |
| Сбой | 16 | 17 | 17 | `/teleop_turtle` | не приходит | 124 |
| После | 16 | 16 | 16 | `/teleop_turtle`, `/turtlesim` | приходит | 0 |

## 3. Причина

`ROS_DOMAIN_ID` задаёт домен DDS — область, в которой участники находят друг друга (discovery). От номера домена зависят сетевые порты обнаружения, поэтому участники из домена 17 не видят участников домена 16: ни нод, ни топиков. Teleop в домене 17 публиковал `/turtle1/cmd_vel` в «пустоту», а CLI-подписчик в домене 17 не нашёл издателя `/turtle1/pose`.

Значение домена читается один раз, при запуске процесса. `export` меняет только переменную оболочки для процессов, которые будут запущены после него, а на уже работающую ноду не влияет. Поэтому teleop пришлось перезапустить, и проверка каждый раз запускалась новым процессом.

Симулятор весь опыт работал в домене 16, и с ним всё было в порядке, а установка ROS исправна (в исходном домене граф работал до сбоя и после). Сбой был в параметре запуска одного участника, а не в программах. Поэтому для восстановления хватило перезапустить teleop и CLI с исходным доменом, а симулятор и установку ROS менять не потребовалось.
