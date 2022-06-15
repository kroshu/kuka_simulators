#!/usr/bin/env python3

import sys
import socket
import time
import xml.etree.ElementTree as ET
import numpy as np

import errno
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rcl_interfaces.msg import ParameterDescriptor
        
def create_rsi_xml_rob(act_joint_pos, setpoint_joint_pos, timeout_count, ipoc):
    q = act_joint_pos
    qd = setpoint_joint_pos
    root = ET.Element('Rob', {'TYPE':'KUKA'})
    ET.SubElement(root, 'RIst', {'X':'0.0', 'Y':'0.0', 'Z':'0.0',
                                'A':'0.0', 'B':'0.0', 'C':'0.0'})
    ET.SubElement(root, 'RSol', {'X':'0.0', 'Y':'0.0', 'Z':'0.0',
                                'A':'0.0', 'B':'0.0', 'C':'0.0'})
    ET.SubElement(root, 'AIPos', {'A1':str(q[0]), 'A2':str(q[1]), 'A3':str(q[2]),
                                'A4':str(q[3]), 'A5':str(q[4]), 'A6':str(q[5])})
    ET.SubElement(root, 'ASPos', {'A1':str(qd[0]), 'A2':str(qd[1]), 'A3':str(qd[2]),
                                'A4':str(qd[3]), 'A5':str(qd[4]), 'A6':str(qd[5])})
    ET.SubElement(root, 'Delay', {'D':str(timeout_count)})
    ET.SubElement(root, 'IPOC').text=str(ipoc)
    return ET.tostring(root)

def parse_rsi_xml_sen(data):
    root = ET.fromstring(data)
    AK = root.find('AK').attrib
    desired_joint_correction = np.array([AK['A1'], AK['A2'], AK['A3'],
                                        AK['A4'], AK['A5'], AK['A6']]).astype(np.float64)
    IPOC = root.find('IPOC').text
    return desired_joint_correction, int(IPOC)

class RSISimulator(Node):
    cycle_time = 0.004
    act_joint_pos = np.array([0, -90, 90, 0, 90, 0]).astype(np.float64)
    initial_joint_pos = act_joint_pos.copy()
    des_joint_correction_absolute = np.zeros(6)
    timeout_count = 0
    ipoc = 0
    rsi_ip_address_ = '127.0.0.1'
    rsi_port_address_ = 59152
    rsi_send_name_ = 'IamFree'
    rsi_act_pub_ = None
    rsi_cmd_pub_ = None
    node_name_ = 'rsi_simulator_node'
    socket_ = None

    def __init__(self, node_name):
        super().__init__(node_name)
        node_name_ = node_name
        self.timer = self.create_timer(self.cycle_time, self.timer_callback)
        rsi_ip_address_descriptor = ParameterDescriptor(description='The ip address of the RSI control interface')
        rsi_port_address_descriptor = ParameterDescriptor(description='The port of the RSI control interface')
        # rsi_port_address_descriptor = ParameterDescriptor(description='The port of the RSI control interface')
        self.declare_parameter('rsi_ip_address_', '127.0.0.1')
        self.declare_parameter('rsi_port_', 59152)
        self.declare_parameter('rsi_send_name_', "IamFree")
        self.rsi_ip_address_ = self.get_parameter('rsi_ip_address_').get_parameter_value().string_value
        self.rsi_port_address_ = self.get_parameter('rsi_port_').get_parameter_value().integer_value
        self.rsi_send_name_ = self.get_parameter('rsi_send_name_').get_parameter_value().string_value
        self.rsi_act_pub_ = self.create_publisher(String, self.node_name_ + '/rsi/state', 1)
        self.rsi_cmd_pub_ = self.create_publisher(String, self.node_name_ + '/rsi/command', 1)
        self.get_logger().info('rsi_ip_address_: {}'.format(self.rsi_ip_address_))
        self.get_logger().info('rsi_port_: {}'.format(self.rsi_port_address_))

        try:
            self.socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.get_logger().info('{}, Successfully created socket'.format(self.node_name_))
            self.socket_.settimeout(1)
        except socket_.error as e:
            self.get_logger().fatal('{} Could not create socket'.format(self.node_name_))
            sys.exit()



    def timer_callback(self):
        try:
            msg = create_rsi_xml_rob(self.act_joint_pos, self.initial_joint_pos, self.timeout_count, self.ipoc)
            self.rsi_act_pub_.publish(msg)
            self.socket_.sendto(msg, (self.rsi_ip_address_, self.rsi_port_address_))
            recv_msg, addr = self.socket_.recvfrom(1024)
            self.rsi_cmd_pub_.publish(recv_msg)
            des_joint_correction_absolute, ipoc_recv = parse_rsi_xml_sen(recv_msg)
            self.act_joint_pos = self.initial_joint_pos + des_joint_correction_absolute
            self.ipoc += 1
            time.sleep(self.cycle_time / 2)
        except OSError as msg:
            self.get_logger().warn('{}: Socket timed out'.format(self.node_name_))
            self.timeout_count += 1
        except self.socket_.error as e:
            if e.errno != errno.EINTR:
                raise

    def on_shutdown(self):
        self.socket_.close()
        node.get_logger().info('Socket closed.')

def main():
    # import argparse

    
    # parser = argparse.ArgumentParser(description='KUKA RSI Simulation')
    # parser.add_argument('rsi_ip_address_', help='The ip address of the RSI control interface')
    # parser.add_argument('rsi_port_address_', help='The port of the RSI control interface')
    # parser.add_argument('--sen', default='ImFree', help='Type attribute in RSI XML doc. E.g. <Sen Type:"ImFree">')
    # Only parse known arguments
    # args, _ = parser.parse_known_args()
    # host = args.rsi_ip_address_
    # port = int(args.rsi_port_address_)
    # sen_type = args.sen
    node_name = 'rsi_simulator_node'

    rclpy.init()
    node = RSISimulator(node_name)
    node.get_logger().info('{}: Started'.format(node_name))
  
    rclpy.spin(node)
    node.on_shutdown()
    node.get_logger().info('{}: Shutting down'.format(node_name))

if __name__ == '__main__':
    main()

    