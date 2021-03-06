# Copyright 2022 Márton Antal
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.from launch import LaunchDescription

from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.descriptions import ParameterValue
from ament_index_python.packages import get_package_share_path

from launch_ros.actions import Node


def generate_launch_description():
    robot_description_path = (get_package_share_path('kuka_kr6_support') /
                              'urdf' / 'kr6r900sixx.xacro')
    rviz_config_path = get_package_share_path('kuka_kr6_support') / 'rviz' / 'rviz.rviz'

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': ParameterValue(
            Command(['xacro ', str(robot_description_path)]), value_type=str
        )}],
        remappings=[("joint_states", "rsi_joint_state")]
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{'use_gui': True}]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', str(rviz_config_path)],
    )

    return LaunchDescription([
        robot_state_publisher_node,
        joint_state_publisher_node,
        rviz_node
    ])
