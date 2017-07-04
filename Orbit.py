import math
import time
import krpc
from threading import *
from execute_maneuver import execute_next_maneuver

def check_solid_fuel(vessel, fuel_stream):
    srbs_separated = False
    while True:
        # Separate SRBs when finished
        if not srbs_separated:
            if fuel_stream() < 0.1:
                vessel.control.activate_next_stage()
                srbs_separated = True
                print('SRBs separated')
                #vessel.control.rcs = True
                vessel.control.throttle = 0.7
                break

        time.sleep(0.1)


def run(target_altitude=400000, n_stages=4):
    turn_start_altitude = 0.001 * target_altitude
    turn_end_altitude = 0.25 * target_altitude

    conn = krpc.connect(name='Launch into orbit')
    vessel = conn.space_center.active_vessel

    # Set up streams for telemetry
    ut = conn.add_stream(getattr, conn.space_center, 'ut')
    altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
    srb_resources = vessel.resources_in_decouple_stage(stage=(n_stages-2), cumulative=False)
    srb_fuel = conn.add_stream(srb_resources.amount, 'SolidFuel')

    srb_thread = Thread(target=check_solid_fuel, args=(vessel, srb_fuel))
    srb_thread.start()

    # Pre-launch setup
    vessel.control.sas = True
    vessel.control.rcs = False
    vessel.control.throttle = 1.0

    # Countdown...
    print('3...')
    time.sleep(1)
    print('2...')
    time.sleep(1)
    print('1...')
    time.sleep(1)
    print('Launch!')

    # Activate the first stage
    vessel.control.activate_next_stage()
    time.sleep(5)

    vessel.auto_pilot.engage()
    time.sleep(1)

    vessel.auto_pilot.target_pitch_and_heading(90, 90)

    # Main ascent loop
    turn_angle = 0
    while True:

        # Gravity turn
        if altitude() > turn_start_altitude and altitude() < turn_end_altitude:
            frac = ((altitude() - turn_start_altitude) /
                    (turn_end_altitude - turn_start_altitude))
            new_turn_angle = frac * 90
            if abs(new_turn_angle - turn_angle) > 0.5:
                turn_angle = new_turn_angle
                vessel.auto_pilot.target_pitch_and_heading(90-turn_angle, 90)

        # Decrease throttle when approaching target apoapsis
        if apoapsis() > target_altitude*0.9:
            print('Approaching target apoapsis')
            break

        time.sleep(0.01)

    # Disable engines when target apoapsis is reached
    vessel.control.throttle = 0.25
    while apoapsis() < target_altitude:
        pass
    print('Target apoapsis reached')
    vessel.control.throttle = 0.0

    # Wait until out of atmosphere
    print('Coasting out of atmosphere')
    while altitude() < 70500:
        pass

    # Plan circularization burn (using vis-viva equation)
    print('Planning circularization burn')
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(
        ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

    vessel.auto_pilot.disengage()
    execute_next_maneuver(conn)

    srb_thread.join()
    print('Launch complete')


if __name__ == '__main__':
    run(target_altitude=350000, n_stages=6)
