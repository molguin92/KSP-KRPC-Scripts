import math
import time
import krpc

def execute_next_maneuver(conn=krpc.connect(name='Execute next maneuver')):
    vessel = conn.space_center.active_vessel
    ut = conn.add_stream(getattr, conn.space_center, 'ut')

    nodes = vessel.control.nodes

    if len(nodes) == 0:
        print('No planned maneuvers!')
        print('Exiting')
        return

    node = nodes[0]
    delta_v = node.delta_v

    # Calculate burn time (using rocket equation)
    print('Calculating burn time...')
    F = vessel.available_thrust
    Isp = vessel.specific_impulse * 9.82
    m0 = vessel.mass
    m1 = m0 / math.exp(delta_v / Isp)
    flow_rate = F / Isp
    burn_time = (m0 - m1) / flow_rate
    print('Burn time: {}s'.format(burn_time))

    # Orientate ship
    print('Orientating ship for planned maneuver')
    vessel.control.rcs = True
    vessel.control.sas = True
    time.sleep(1)
    vessel.control.sas_mode = conn.space_center.SASMode.maneuver
    time.sleep(1)

    while 1.0 - vessel.direction(node.reference_frame)[1] > 0.0001:
        print(vessel.direction(node.reference_frame))
        time.sleep(.1)

    # Wait until burn
    print('Waiting until burn')
    burn_ut = ut() + node.time_to - (burn_time/2.)
    lead_time = 5 # buffer time for orientation
    conn.space_center.warp_to(burn_ut - lead_time)

    print(vessel.direction(node.reference_frame))


    # Execute burn
    print('Ready to execute burn... Waiting')
    while node.time_to - (burn_time/2.) > 0:
        time.sleep(.1)
        pass

    print(vessel.direction(node.reference_frame))
    print('Executing burn')
    vessel.control.throttle = 1.0

    while node.remaining_delta_v >= 10.0:
        time.sleep(.1)
        pass

    print('Fine tuning')
    vessel.control.throttle = 0.05
    remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
    while remaining_burn()[1] > 0.1:
        time.sleep(.1)
        pass
    vessel.control.throttle = 0.0
    node.remove()

    print('Maneuver done!')


if __name__ == '__main__':
    execute_next_maneuver()
