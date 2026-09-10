# SumoBot v2 -- turn the four IR sensors into a direction vector.
#
# The sensors sit at the corners of a square:
#
#         s1 ----- s2          +y is towards s1/s2 (the top)
#          |       |           +x is towards s2/s4 (the right)
#         s3 ----- s4
#
# If the surface under them shades smoothly from one side to the other, those
# four numbers describe a tilted plane, and the steepest-uphill direction of that
# plane is a vector. Averaging the two sensors on each side and subtracting gives
# it directly -- two points per axis is exactly enough to define a slope, so
# there is nothing to fit.
#
#     from sumobotv2 import SumoBotV2
#     from ir_gradient import ir_gradient
#
#     sumo = SumoBotV2()
#     x, y, strength, degrees = ir_gradient(sumo.infrared)

import math


def ir_gradient(infrared):
    """Direction of increasing reflectance: (x, y, strength, degrees).

    Takes the list sumo.infrared returns, [s1, s2, s3, s4].

        x, y       the vector. Each -1.0 to +1.0.
        strength   how pronounced the slope is, 0.0 to 1.0.
        degrees    the same direction as an angle: 0 is right, 90 is forward,
                   180 is left, -90 is back.

    The vector points towards LARGER sensor readings. Whether larger means the
    light part of the surface or the dark part depends on your sensors, not on
    this maths -- check it once on a real edge and remember which way round it is.

    Divided by the total of all four, so the result does not change when the
    whole surface gets brighter or the robot rides a little higher. Same reason
    color() normalizes.

    CHECK strength BEFORE USING degrees. Over a uniform surface the gradient is
    only sensor noise, and its direction is meaningless however confident the
    number looks. Pick your cutoff by reading strength over a blank patch and
    taking a few times the worst value you see.

    Returns (0.0, 0.0, 0.0, 0.0) if all four read zero.
    """
    s1, s2, s3, s4 = infrared
    total = s1 + s2 + s3 + s4
    if not total:
        return (0.0, 0.0, 0.0, 0.0)

    x = ((s2 + s4) - (s1 + s3)) / total   # right minus left
    y = ((s1 + s2) - (s3 + s4)) / total   # top minus bottom

    return (x, y, math.sqrt(x * x + y * y), math.degrees(math.atan2(y, x)))
