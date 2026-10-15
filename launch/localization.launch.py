import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
)
from launch_ros.actions import PushRosNamespace
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from nav2_common.launch import RewrittenYaml


def generate_launch_description():

    # Packages
    pkg_ridgeback_nav2 = get_package_share_directory('ridgeback_nav2')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    # Launch arguments
    map_file = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    scan_topic = LaunchConfiguration('scan_topic')

    # Ridgeback localization parameters
    localization_params = os.path.join(
        pkg_ridgeback_nav2,
        'config',
        'localization.yaml'
    )

    # Allow scan topic to be changed without editing localization.yaml
    rewritten_params = RewrittenYaml(
        source_file=localization_params,
        param_rewrites={
            'scan_topic': scan_topic,
        },
        convert_types=True
    )

    # Nav2 localization launch file
    nav2_localization_launch = os.path.join(
        pkg_nav2_bringup,
        'launch',
        'localization_launch.py'
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_localization_launch),
        launch_arguments={
            'namespace': 'r100_0165',
            'map': map_file,
            'use_sim_time': use_sim_time,
            'params_file': rewritten_params,
        }.items()
    )

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            choices=['true', 'false'],
            description='Use simulation time'
        ),

        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(
                pkg_ridgeback_nav2,
                'maps',
                'nav_map.yaml'
            ),
            description='Full path to map YAML file'
        ),

        DeclareLaunchArgument(
            'scan_topic',
            default_value='sensors/lidar2d_0/scan',
            description='2D laser scan topic used by AMCL'
        ),

        GroupAction([
            PushRosNamespace('r100_0165'),
            localization,
        ]),
    ])