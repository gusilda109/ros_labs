# ПР03. Первая нода — поза и команда

Опыт выполнен в Docker с ROS 2 Lyrical. Для замера использован отдельный симулятор в домене `36`, чтобы исключить влияние открытого симулятора в домене `16`. Для показа откройте рабочий стол Ubuntu через [noVNC](http://localhost:6080/) и повторите опыт в трёх терминалах. Во всех трёх используйте один домен. Остановите teleop в этом домене, если он запущен.

## Сборка и запуск

**Терминал Ubuntu A — сборка и симулятор**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=36
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
ros2 launch turtle_bringup sim.launch.py
```

**Терминал Ubuntu B — patrol до remap**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=36
ros2 run patrol patrol
```

**Терминал Ubuntu C — наблюдение до remap**

```bash
cd /home/ubuntu/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=36
ros2 topic type /turtle1/pose
ros2 node info /patrol
ros2 topic info /cmd_vel --verbose
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic echo /cmd_vel --once
ros2 topic echo /turtle1/pose --once
sleep 1
ros2 topic echo /turtle1/pose --once
```

Тип позы — `turtlesim_msgs/msg/Pose`. Ещё до remap `/patrol` получает позу и выдаёт `Twist` со значениями `linear.x=0.5` и `angular.z=0.3`. Обе записи позы дали `x=5.54444`, `y=5.54444`, `theta=0` и нулевые скорости. Относительное имя `cmd_vel` у ноды в корневом пространстве имён разрешается в `/cmd_vel`. Симулятор подписан на `/turtle1/cmd_vel`. Граф фиксирует разрыв.

| Сценарий | Топик | Издатели | Подписчики |
| --- | --- | ---: | ---: |
| До remap | `/cmd_vel` | 1 (`/patrol`) | 0 |
| До remap | `/turtle1/cmd_vel` | 0 | 1 (`/turtlesim`) |
| После remap | `/turtle1/cmd_vel` | 1 (`/patrol`) | 1 (`/turtlesim`) |

## Remap и измерение

**Терминал Ubuntu B — patrol после remap**

Нажмите `Ctrl+C`, дождитесь завершения предыдущего запуска и в том же терминале выполните команду.

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

**Терминал Ubuntu C — наблюдение после remap**

```bash
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic echo /turtle1/cmd_vel --once
ros2 topic echo /turtle1/pose --once
timeout -s INT 10s ros2 topic hz /turtle1/cmd_vel
ros2 topic echo /turtle1/pose --once
```

После remap черепашка двигалась по дуге. Два сообщения позы во время движения дали `(x, y, theta)` около `(6.997, 6.401, 1.061)` и `(3.875, 7.277, -1.613)`. Измерение длилось 10 секунд. Последняя строка `ros2 topic hz` показала `9.999` Гц, интервалы `0.092–0.107` с и `window: 90`. Код `124` у `timeout` ожидаем по окончании замера.

**Терминал Ubuntu B — завершение ноды**

Нажмите `Ctrl+C` в B. Симулятор в A продолжит публиковать позу.

**Терминал Ubuntu C — проверка остановки**

```bash
ros2 topic echo /turtle1/pose --once
sleep 2
ros2 topic echo /turtle1/pose --once
sleep 1
ros2 topic echo /turtle1/pose --once
```

После завершения `patrol` три замера показали одинаковую позу `(3.966, 6.663, -1.238)` и нулевые линейную и угловую скорости. После проверки остановите симулятор через `Ctrl+C` в A.

## Что делает нода

`init()` подготавливает контекст ROS 2. `spin()` запускает обработку событий, пока работает нода. Callback подписки сохраняет последнюю позу. Callback таймера каждые `0.1` с выбирает команду через `command_for_pose()` и публикует `Twist`. Пока позы нет, все компоненты команды равны нулю. При полученной позе нода публикует `linear.x=0.5` и `angular.z=0.3`.

`Ctrl+C` посылает `SIGINT`. Контекст ROS 2 завершает работу, `spin()` выходит, нода освобождает ресурсы и поток команд прекращается. turtlesim ещё некоторое время движется по последней полученной команде, затем самостоятельно обнуляет скорости по таймауту. Остановку подтверждают нулевые скорости и совпадающие значения позы в последовательных сообщениях.

## Проверка тестами

**Терминал Ubuntu C — тесты из корня workspace с уже подключённым окружением**

```bash
python3 -m pytest src/patrol/test
python3 .course-kit/v1/tools/check_practice.py PR03 --submission .
```

В `tests.txt` сохранён вывод сборки и pytest. Два теста проверяют весь `Twist` для отсутствующей и полученной позы. В сгенерированном наборе проверка `ament_copyright` помечена как пропускаемая.

В отчёте учтено время подготовки и автоматической проверки. Время лабораторной пары не учитывалось.
