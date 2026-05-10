# Swerve ROS2驱动

## 依赖

- ROS2 `>= Humble`

```bash
sudo apt update
sudo apt install -y \
    libdw-dev \
    libnlopt-cxx-dev \
    ros-${ROS_DISTRO}-moveit \
    ros-${ROS_DISTRO}-moveit-ros-perception \
    ros-${ROS_DISTRO}-ros2-control \
    ros-${ROS_DISTRO}-backward-ros \
    ros-${ROS_DISTRO}-xacro
```

请注意，Moveit配置文件里默认配置了`TRAC-IK`作为运动学求解器，但直到Jazzy版本之后，它才进入了ROS2的官方源，若在ROS2 Humble下使用，请一并编译 `src/` 目录下的 `trac_ik` 包，若使用ROS2 Jazzy或更高版本，则请在 `src/trac_ik` 目录下新建一个空的 `COLCON_IGNORE` 文件跳过编译，并：

```
sudo apt update
sudo apt install -y ros-${ROS_DISTRO}-trac-ik*
```
