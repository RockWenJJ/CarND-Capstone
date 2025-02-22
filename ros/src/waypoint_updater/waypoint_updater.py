#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint
from std_msgs.msg import Int32
from scipy.spatial import KDTree

import math
import numpy as np


'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 100 # Number of waypoints we will publish. You can change this number
MAX_DECEL     = 1.0


class WaypointUpdater(object):
    def __init__(self):
        rospy.init_node('waypoint_updater')

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below
        rospy.Subscriber('/traffic_waypoint', Int32, self.traffic_cb)

        self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)

        # TODO: Add other member variables you need below
        self.waypoints_list = None
        self.waypoints_2d   = None
        self.kdtree         = None
        self.pose           = None
        self.stopline_wp_idx= -1
        self.loop()


        rospy.spin()

    def pose_cb(self, msg):
        # TODO: Implement
        self.pose = msg.pose

    def waypoints_cb(self, waypoints):
        # TODO: Implement
        self.waypoints_list = waypoints
        if not self.waypoints_2d:
            self.waypoints_2d = [[waypoint.pose.pose.position.x, waypoint.pose.pose.position.y] for waypoint in waypoints.waypoints]
            self.kdtree = KDTree(self.waypoints_2d)

    def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement
        self.stopline_wp_idx = msg.data

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass

    def get_waypoint_velocity(self, waypoint):
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        dist = 0
        dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
        for i in range(wp1, wp2+1):
            dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
            wp1 = i
        return dist
    def get_closest_waypoint_idx(self):
        x = self.pose.position.x
        y = self.pose.position.y
        closest_index = self.kdtree.query([x, y], 1)[1]
        closest_coord = self.waypoint2_2d[closest_index]
        previous_coord= self.waypoints_2d[closest_index - 1]

        cl_vect = np.array(closest_coord)
        pr_vect = np.array(previous_coord)
        cr_vect = np.array([x, y])

        val = np.dot(cl_vect - pr_vect, cl_vect - cr_vect)
        if val < 0:
            closest_index = (closet_index + 1) % len(self.waypoints_2d)
        return closest_index

    def pulish_waypoints(self, index):
        lane = Lane()
        lane.header = self.waypoints_list.header

        farthest_idx = index + LOOKAHEAD_WPS
        base_waypoints = self.waypoints_list.waypoints[index:farthest_idx]

        if self.stopline_wp_idx == -1 or (self.stopline_wp_idx >= farthest_idx):
            lane.waypoints = base_waypoints
        else:
            lane.waypoints = self.decelerate_waypoints(base_waypoints, index)
        self.final_waypoints_pub.publish(lane)

    def decelerate_waypoints(self, waypoints, closest_idx):
        new_waypoints = []
        for i, wp in enumerate(waypoints):
            p = Waypoint()
            p.pose = wp.pose

            stop_idx = max(self.stopline_wp_idx - closest_idx - 2, 0)
            dist = self.distance(waypoints, i, stop_idx)
            vel = math.sqrt(2 * MAX_DECEL * dist)
            if vel < 1.0:
                vel = 0.0
            p.twist.twist.linear.x = min(vel, wp.twist.twist.linear.x)
            new_waypoints.append(x)

        return new_waypoints

    def loop(self):
        rate = rospy.Rate(50)
        while not rospy.is_shutdown():
            if self.pose and self.kdtree:
                closest_point_index = self.get_closest_waypoint_idx()
                self.publish_waypoints(closet_point_index)
            rate.sleep()


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')
