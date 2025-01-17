#!/usr/bin/env python2
"""
unit_03
GraphNavigator.py
"""

import rospy
from std_msgs.msg import String, Header
from sensor_msgs.msg import LaserScan, PointCloud
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped, PointStamped, Point32, Point
from visualization_msgs.msg import MarkerArray, Marker
import tf_conversions as conversions
import numpy as np
from Graph import Graph, dist
from typing import Tuple
import math
import os


ROBO_NAME = "GraphNavigator.py"
LOG_FILE = "GraphNavigator.log"

EDGE_FILE = "kanten_prakt_01.txt"
VERTEX_FILE = "knoten_prakt_01.txt"

DIST_FRESHHOLD = 0.3
VIRTUAL_VERTEXT_NUM = -666

def quaternionMsgToEuler(quaternionMsg):
    return conversions.transformations.euler_from_quaternion((quaternionMsg.x, quaternionMsg.y, quaternionMsg.z, quaternionMsg.w))

class GraphNavigator:
    def __init__(self):
        rospy.init_node('emil', anonymous=True)
        self.laserData = None
        #self.amclPos = None
        self.laserSubscriber = rospy.Subscriber('laserscan', LaserScan, queue_size=20, callback=self.laserCallback)
        #self.amclPosSubscriber = rospy.Subscriber('amcl_pose', PoseWithCovarianceStamped, queue_size=20, callback=self.amclPosCallback)
        #self.clickedPointSubscriber = rospy.Subscriber('clicked_point', PointStamped, queue_size=20, callback=self.clickedPointCallback)
        self.commandPublisher = rospy.Publisher('cmd_vel', Twist, queue_size=20)
        #self.graphVizPublisher = rospy.Publisher('visualization_marker_array', MarkerArray, queue_size=20)
        self.roombaCommand = Twist()
        #self.graph = Graph.formFiles(VERTEX_FILE, EDGE_FILE)
        self.steps = []
        self.loggedReachedTarget = False

    def laserCallback(self, laserData):
        # rospy.loginfo(f'got laserData {laserData.ranges}')
        self.laserData = np.fromiter(laserData.ranges, dtype=float)
        """
    def amclPosCallback(self, amcPos):
        self.amclPos = amcPos

    def clickedPointCallback(self, pointStamped):
        point = pointStamped.point
        self.initializeNavigationTo(point.x, point.y)

    def readLaser(self):
        pass
        """
    def emergencyStop(self):
        if self.laserData is None:
            return

        if self.laserData.min() <= 0.3:
            self.roombaCommand.linear.x = 0.0
            self.roombaCommand.angular.z = 0.0
            rospy.loginfo(f'{ROBO_NAME} stopped by emergencyStop\n')

    def calculateCommand(self):
        if self.laserData is None or len(self.laserData) < 540 or self.amclPos is None:
            return

        curX, curY, curYaw = self.simpleAmclPose

        with open(LOG_FILE, mode="a") as f:
            f.write(f"{curX} {curY} {math.degrees(curYaw)}\n")
        # rospy.loginfo(f"{ROBO_NAME} amclPos: x={curX},y={curY},yaw={math.degrees(curYaw)}")

        # we are at the target so don't move
        if len(self.steps) == 0:
            if not self.loggedReachedTarget:
                rospy.loginfo(f"{ROBO_NAME} reached target")
                self.loggedReachedTarget = True
            self.roombaCommand.linear.x = 0
            self.roombaCommand.angular.z = 0
            return

        targetX = self.steps[0].x
        targetY = self.steps[0].y
        distance = dist(targetX, targetY, curX, curY)
        if distance < DIST_FRESHHOLD:
            self.steps.pop(0)
            return self.calculateCommand

        # carfull the arguments are reversed for np.arctan2 -> np.arctan2(y, x)
        targetYaw = np.arctan2(targetY - curY, targetX - curX)

        # rospy.loginfo(f"{ROBO_NAME} targeting ({targetX}, {targetY}, {math.degrees(targetYaw)}°), dist={dist}")
        yawDiff = targetYaw - curYaw
        # set the roomba velocities
        # the linear velocity (front direction is x axis) is measured in m/sec
        # the angular velocity (around z axis, yaw) is measured in rad/sec
        self.roombaCommand.linear.x = 0.2 * (abs(yawDiff) < math.radians(5))
        self.roombaCommand.angular.z = 0.3 * np.tanh(yawDiff)

        """
    @property
    def simpleAmclPose(self) -> Tuple[float, float, float]:
        pose = self.amclPos.pose.pose
        x = pose.position.x
        y = pose.position.y
        (_, _, yaw) = quaternionMsgToEuler(pose.orientation)
        return x, y, yaw

    def initializeNavigationTo(self, x, y):
        curX, curY, _ = self.simpleAmclPose
        start = self.graph.vertexClosestTo(curX, curY)
        end = self.graph.vertexClosestTo(x, y)
        steps = self.graph.findPath(start, end)
        if steps is None:
            rospy.logwarn(f"No path from {start} to {end}")
            self.steps = []
            return
        self.steps = steps
        # append destianation
        self.steps.append(Graph.Vertex(self.graph, VIRTUAL_VERTEXT_NUM, x, y))
        # do some logging
        rospy.loginfo(f"{ROBO_NAME} starting at {start}")
        rospy.loginfo(f"{ROBO_NAME} ending at {end}")
        rospy.loginfo(f"{ROBO_NAME} using rout {self.steps}")
        self.loggedReachedTarget = False

    def publishGraph(self):

        def newMarker():
            marker = Marker()
            marker.header.frame_id = 'map'
            marker.header.stamp = rospy.Time.now()
            marker.ns = "nav_graph"
            return marker

        def createNodeMarker(vertex: Graph.Vertex):
            marker = newMarker()
            marker.id = vertex.num
            marker.type = Marker.TEXT_VIEW_FACING
            marker.action = Marker.ADD
            marker.pose.position.x = vertex.x
            marker.pose.position.y = vertex.y
            marker.pose.position.z = 1
            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0
            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = 0.2
            marker.color.a = 1.0
            marker.color.r = 0.0
            marker.color.g = 0.0
            marker.color.b = 0.0
            marker.text = str(vertex.num)
            return marker

        def createEdgeMarker(edge: Graph.Edge):
            marker = newMarker()
            marker.id = edge.num + len(self.graph.vertices)
            marker.type = Marker.ARROW
            marker.action = Marker.ADD
            start = edge.start
            end = edge.end
            marker.points = [Point(x=start.x, y=start.y), Point(x=end.x, y=end.y)]

            marker.scale.x = 0.03
            marker.scale.y = 0.1
            marker.scale.z = 0.07
            marker.color.a = 1.0
            marker.color.r = 173 / 255
            marker.color.g = 216 / 255
            marker.color.b = 230 / 255
            return marker

        markerArray = MarkerArray()
        markers = [createNodeMarker(v) for v in self.graph.vertices] + [createEdgeMarker(e) for e in self.graph.edges]
        markerArray.markers = markers
        self.graphVizPublisher.publish(markerArray)

"""
    def mainLoop(self):
        rate = rospy.Rate(20)

        while not rospy.is_shutdown():
            # Sense
            #self.readLaser()

            # Model
            # no modeling necessary for this simple job

            # Plan
            self.calculateCommand()

            #rospy.loginfo(f'{ROBO_NAME} movement commands:forward speed={self.roombaCommand.linear.x}[m/sec]' +
            #    f'and turn speed={self.roombaCommand.angular.z}[rad/sec]')

            # Act
            self.emergencyStop()

            self.commandPublisher.publish(self.roombaCommand)

            self.publishGraph()
            rate.sleep()

if __name__ == '__main__':
    try:
        os.remove(LOG_FILE)
    except OSError:
        pass
    GraphNavigator().mainLoop()
