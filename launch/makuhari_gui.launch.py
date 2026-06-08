import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    rviz_config_dir = os.path.join(
        get_package_share_directory('makuhari_gui'),
        'rviz',
        'makuhari.rviz'
    )
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_dir],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    delayed_display_nodes = TimerAction(
        period=2.0,
        actions=[
            Node(
                package='makuhari_gui',
                executable='navigation_mode_display_node',
                name='navigation_mode_display_node',
                output='screen',
            ),
            Node(
                package='makuhari_gui',
                executable='vital_display_node',
                name='vital_display_node',
                output='screen',
            ),
            Node(
                package='makuhari_gui',
                executable='tatto_display_node',
                name='tatto_display_node',
                output='screen',
            ),
        ]
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        rviz_node,
        delayed_display_nodes
    ])