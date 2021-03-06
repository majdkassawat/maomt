#! /usr/bin/python2
import rospy
import time
import sys
from std_msgs.msg import Int64

EMULATE_HX711 = False

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711


def cleanAndExit():
    print "Cleaning..."

    if not EMULATE_HX711:
        GPIO.cleanup()

    print "Bye!"
    sys.exit()


hx_right = HX711(6, 5)


# I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
# Still need to figure out why does it change.
# If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
# There is some code below to debug and log the order of the bits and the bytes.
# The first parameter is the order in which the bytes are used to build the "long" value.
# The second paramter is the order of the bits inside each byte.
# According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
hx_right.set_reading_format("MSB", "MSB")


# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
# hx.set_reference_unit(113)
hx_right.set_reference_unit(200)


hx_right.reset()


# hx_right.tare()

# print "Tare done! Add weight now..."

# to use both channels, you'll need to tare them both
# hx_right.tare_A()
# hx_right.tare_B()


rospy.init_node('force_sensor_interface_right', log_level=rospy.INFO)
force_sensor_right_pub = rospy.Publisher(
    'force_sensor_right', Int64, queue_size=1)

force_sensor_right_msg = Int64()


r = rospy.Rate(30)

current_sample = 0
previous_sample = 0
last_good_sample = 0
output = 0
alpha = 0.1
weight_offset = 0
weight_offset = hx_right.get_weight(2)
while not rospy.is_shutdown():

    val_right = hx_right.get_weight(2) - weight_offset

    current_sample = val_right

    if current_sample < 0:
        last_good_sample = 0
        output = last_good_sample
    elif current_sample > 1000:
        output = last_good_sample
    else:
        diff = abs(current_sample - previous_sample)
        if diff > 300:
            output = last_good_sample
        else:
            last_good_sample = current_sample
            output = last_good_sample
    output = output * alpha + (1 - alpha) * previous_sample
    previous_sample = output

    force_sensor_right_msg.data = output
    force_sensor_right_pub.publish(force_sensor_right_msg)

    r.sleep()

cleanAndExit()