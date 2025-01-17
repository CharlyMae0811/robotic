#!/usr/bin/env python2
#### guess_03
import sys
import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Twist
##from sensor_msgs.msg import LaserScan

class guess_03:
    """docstring fs guess_03."""

    def __init__(self):
        rospy.init_node("guess_03", anonymous=True)
        self.bridge = CvBridge()
        self.cv_image = None
        self.image_sub = rospy.Subscriber("/cv_camera/image_raw",Image,self.callback)
        #self.laserSubscriber = rospy.Subscriber('laserscan', LaserScan, queue_size=20, callback=self.laserCallback)

        self.commandPublisher = rospy.Publisher('cmd_vel', Twist, 20)
        self.roombaCommand = Twist()

    def callback(self,data):

        rospy.loginfo("data image \n")
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
            self.cv_image = cv_image

        except CvBridgeError as e:
            print(e)
            ROS_INFO(e)

    def imagecolor(self):
        cv_image = self.cv_image
        if cv_image is None:
            return
        (rows,cols,channels) = cv_image.shape
        if cols > 20 and rows > 20:
            #--- Circle
            cv2.circle(cv_image, (500,500), 200, 255)

            #--- Text
            text = "Samir"
            cv2.putText(cv_image, text, (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, [0,0,200], 5)

        #--- Optional: show the image on a window (comment this for the Raspberry Pi)
        cv2.imshow("Image window", cv_image)
        cv2.waitKey(3)

    def calculateCommand(self):
        self.roombaCommand.linear.x = 0.3
        self.roombaCommand.angular.z = 0.0

    #def laserCallback(self, laserData):
        # rospy.loginfo(f'got laserData {laserData.ranges}')
        #self.laserData = np.fromiter(laserData.ranges, dtype=float)

    def mainLoop(self):
        rate = rospy.Rate(20)

        while not rospy.is_shutdown():
            #rospy.loginfo(" mainLoop \n")

        #    self.imagecolor()
            self.calculateCommand()
            self.commandPublisher.publish(self.roombaCommand)
            rate.sleep()

        #rate = rospy.Rate(20)
        #guess_03_object = guess_03()
        #rospy.init_node("guess_03", anonymous=True)

        #while not rospy.is_shutdown():

            #self.imagecolor()

            #rate.sleep()
        #guess_03()
        #self.imagecolor()

        #rospy.init_node("guess_03", anonymous=True)
        #try:
        #    rospy.spin()
        #except KeyboardInterrupt:
        #    ROS_INFO("shut down")

def main(args):
    A = guess_03()
    A.mainLoop()
    #A.imagecolor()


if __name__ == '__main__':
    main(sys.argv)
