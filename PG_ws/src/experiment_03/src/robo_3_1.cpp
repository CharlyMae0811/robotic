//
//
// experiment_01
// robo_04
//
// A simple robot control named: robo_3_1
//
// Author: University of Bonn, Autonomous Intelligent Systems
//

// Includes to talk with ROS and all the other nodes
#include <ros/ros.h>
#include <geometry_msgs/Twist.h>
#include <sensor_msgs/LaserScan.h>
#include <sensor_msgs/Joy.h>
#include <geometry_msgs/PoseWithCovarianceStamped.h>
#include <tf/transform_datatypes.h>
#include <geometry_msgs/Quaternion.h>
#include <math.h>

#include <sensor_msgs/image_encodings.h>


// Class definition
class robo_3_1 {
public:
	robo_3_1();
	void laserCallback(const sensor_msgs::LaserScanConstPtr& m_scan_data);
	void amclCallback(const geometry_msgs::PoseWithCovarianceStampedConstPtr& amcl_pose);
	void emergencyStop();
	void calculateCommand();
	void mainLoop();
	void joyCallback(const sensor_msgs::Joy::ConstPtr& joy);

protected:

	// Nodehandle for robo_3_1 robot
	ros::NodeHandle m_nodeHandle;

	// Subscriber and membervariables for our laserscanner
	ros::Subscriber m_laserSubscriber;
	sensor_msgs::LaserScan m_laserscan;

	// Publisher and membervariables for the driving commands
	ros::Publisher m_commandPublisher;
	geometry_msgs::Twist m_roombaCommand;
	
	// AMCL
	ros::Subscriber m_amclSubscriber;
	geometry_msgs::PoseWithCovarianceStamped m_amclPose;
	
	double xpos;
	double ypos;
	double yaw;
	int linear_, angular_;
  	double l_scale_, a_scale_;
  	double fotoclick;
 	ros::Subscriber joy_sub_;

};

// constructor
robo_3_1::robo_3_1() {
	// Node will be instantiated in root-namespace
	ros::NodeHandle m_nodeHandle("/");

	// Initialising the node handle
	m_laserSubscriber  = m_nodeHandle.subscribe<sensor_msgs::LaserScan>("laserscan", 20, &robo_3_1::laserCallback, this);
	m_commandPublisher = m_nodeHandle.advertise<geometry_msgs::Twist> ("cmd_vel", 20);
	
	//Joy
	m_nodeHandle.param("axis_linear", linear_, linear_);
  	m_nodeHandle.param("axis_angular", angular_, angular_);
  	m_nodeHandle.param("scale_angular", a_scale_, a_scale_);
  	m_nodeHandle.param("scale_linear", l_scale_, l_scale_);
	
	joy_sub_ = m_nodeHandle.subscribe<sensor_msgs::Joy>("joy", 10, &robo_3_1::joyCallback, this);
	//AMCL
	m_amclSubscriber = m_nodeHandle.subscribe<geometry_msgs::PoseWithCovarianceStamped> ("amcl_pose", 20, &robo_3_1::amclCallback,this);
	
	
}// end of robo_3_1 constructor

void robo_3_1::joyCallback(const sensor_msgs::Joy::ConstPtr& joy)
{
 m_roombaCommand.linear.x  = l_scale_*joy->buttons[1];
 m_roombaCommand.angular.z = a_scale_*joy->axes[0];
 fotoclick = joy->buttons[2];
 if (fotoclick == 1) {
 m_roombaCommand.linear.x  = l_scale_*(-1);
 }
}


// callback for getting laser values 
void robo_3_1::laserCallback(const sensor_msgs::LaserScanConstPtr& scanData) {
    
	if( (&m_laserscan)->ranges.size() < scanData->ranges.size() ) {
		m_laserscan.ranges.resize((size_t)scanData->ranges.size()); 
    	}

	for(unsigned int i = 0; i < scanData->ranges.size(); i++)
	{
		m_laserscan.ranges[i] = scanData->ranges[i];
	}
}// end of laserCallback

//AMCL Callback
void robo_3_1::amclCallback(const geometry_msgs::PoseWithCovarianceStampedConstPtr& amcl_pose) {
	xpos = amcl_pose->pose.pose.position.x;
	ypos = amcl_pose->pose.pose.position.y;
	
	
	//ausrichtung = amcl_pose->pose.pose.orientation
	yaw = tf::getYaw(amcl_pose->pose.pose.orientation);
	//tf::Matrix3x3(amcl_pose->pose.pose.orientation).getRPY(roll, pitch, yaw);
	
}


// here we go
// this is the place where we will generate the commands for the robot
void robo_3_1::calculateCommand() {

	// please find out what this part of the robot controller is doing
	// watch the robot 
	// look into the source file 
	// and try to deduce the underlying idea

        // see if we have laser data available
	if( (&m_laserscan)->ranges.size() > 0)
          {
		double qs = 0.2 ;
                double qt = 0.0 ; 
                int c_r = 0 ;
                int c_l = 0 ;

                // first part
                for( int i=45;i<=270;i++)
                   if (m_laserscan.ranges[i] < 0.5)
                      c_r++; 

                // second part 
                for( int i=270;i<=490;i++)
                   if (m_laserscan.ranges[i] < 0.7)
                      c_l++ ;


                // third part 
                if (c_l > 5)
                   {
                        qs = 0.1, qt  = -0.25 ;
                   } // end of if

                // fourth part 
                if (c_r > 5)
                   {
                        qs = 0.1 ;
                        qt = +0.3 ;
                   } // end of if


                // set the roomba velocities
                // the linear velocity (front direction is x axis) is measured in m/sec
                // the angular velocity (around z axis, yaw) is measured in rad/sec
                m_roombaCommand.linear.x  = qs ;
                m_roombaCommand.angular.z = qt ;

          } // end of if we have laser data
	  
} // end of calculateCommands

// robot shall stop, in case anything is closer than ... 
void robo_3_1::emergencyStop() {

        // see if we have laser data
 	if( (&m_laserscan)->ranges.size() > 0) 
	{
		for(unsigned int i=0; i < (&m_laserscan)->ranges.size(); i++)
		{
			if( m_laserscan.ranges[i] <= 0.30) {
				m_roombaCommand.linear.x = 0.0;
				m_roombaCommand.angular.z = 0.0;
			}// end of if too close
		}// end of for all laser beams
	} // end of if we have laser data
}// end of emergencyStop



//
void robo_3_1::mainLoop() {
	// determines the number of loops per second
	ros::Rate loop_rate(20);
	
	// als long as all is O.K : run
	// terminate if the node get a kill signal
	while (m_nodeHandle.ok())
	{
		calculateCommand();
		emergencyStop();

		//ROS_INFO(" robot_04 dude runs with: .x=%+6.2f[m/s], .z=%+6.2f[rad/s]", m_roombaCommand.linear.x, m_roombaCommand.angular.z);

		// send the command to the roomrider for execution
		m_commandPublisher.publish(m_roombaCommand);
		ROS_INFO(" Xposition: %f - Yposition: %f Yaw: %f", xpos, ypos, yaw);
		// spinOnce, just make the loop happen once
		ros::spinOnce();
		// and sleep, to be aligned with the 50ms loop rate
		loop_rate.sleep();
	}
}// end of mainLoop


int main(int argc, char** argv) {

	// initialize
	ros::init(argc, argv, "robo_3_1");

	// get an object of type robo_3_1 and call it dude 
	robo_3_1 dude  ;

	// main loop
	// make dude execute it's task 
	dude.mainLoop();

	return 0;

}// end of main

// end of file: robo_04.cpp

