# Software License Agreement (BSD)
#
# @author    Roni Kreinin <rkreinin@clearpathrobotics.com>
# @copyright (c) 2023, Clearpath Robotics, Inc., All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of Clearpath Robotics nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Standard navigation only. Run localization separately before sending goals."""
import os
from ament_index_python.packages import get_package_share_directory
from clearpath_config.clearpath_config import ClearpathConfig
from clearpath_config.common.utils.yaml import read_yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml


def launch_setup(context):
    setup = LaunchConfiguration('setup_path').perform(context)
    config = ClearpathConfig(read_yaml(os.path.join(setup, 'robot.yaml')))
    namespace = config.system.namespace.strip('/')
    prefix = '/' + namespace if namespace else ''
    scan = LaunchConfiguration('scan_topic').perform(context)
    if not scan:
        scan = prefix + '/sensors/lidar2d_0/scan'
    elif not scan.startswith('/'):
        scan = prefix + '/' + scan
    params = ParameterFile(RewrittenYaml(
        source_file=LaunchConfiguration('params_file'), root_key=namespace,
        param_rewrites={'topic': scan, 'map_topic': prefix + '/map',
                        'odom_topic': prefix + '/platform/odom/filtered'},
        convert_types=True), allow_substs=True)
    tf = [('/tf', prefix + '/tf'), ('/tf_static', prefix + '/tf_static')]
    specs = [
        ('nav2_controller', 'controller_server', [('cmd_vel', 'cmd_vel_nav')]),
        ('nav2_planner', 'planner_server', []),
        ('nav2_smoother', 'smoother_server', []),
        ('nav2_behaviors', 'behavior_server', [('cmd_vel', 'cmd_vel_nav')]),
        ('nav2_bt_navigator', 'bt_navigator', []),
        ('nav2_waypoint_follower', 'waypoint_follower', []),
        ('nav2_velocity_smoother', 'velocity_smoother', [('cmd_vel', 'cmd_vel_nav')]),
        ('nav2_collision_monitor', 'collision_monitor', []),
    ]
    nodes = [Node(package=package, executable=name, name=name,
                  namespace=namespace, output='screen',
                  parameters=[params, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
                  remappings=tf + remaps)
             for package, name, remaps in specs]
    nodes.append(Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation', namespace=namespace, output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time'),
                     'autostart': LaunchConfiguration('autostart'),
                     'node_names': [name for _, name, _ in specs]}]))
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('setup_path', default_value='/home/digifocus/clearpath'),
        DeclareLaunchArgument('use_sim_time', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('autostart', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('scan_topic', default_value=''),
        DeclareLaunchArgument('params_file', default_value=os.path.join(
            get_package_share_directory('ridgeback_nav2'), 'config', 'nav2.yaml')),
        OpaqueFunction(function=launch_setup),
    ])
