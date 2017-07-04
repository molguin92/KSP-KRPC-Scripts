import time
import krpc

def run():
    conn = krpc.connect(name='Sub-orbital flight')

    vessel = conn.space_center.active_vessel

    vessel.auto_pilot.target_pitch_and_heading(90, 90)
    vessel.auto_pilot.engage()
    vessel.control.throttle = 0.5
    time.sleep(1)

    print('Countdown...')
    for i in range(5, 0, -1):
        print(str(i))
        time.sleep(1)
    print('Launch!')
    vessel.control.activate_next_stage()

    turn1 = False
    turn2 = True

    while vessel.resources.amount('SolidFuel') > 0.1:
        time.sleep(1)

    print('Booster separation...')
    vessel.control.activate_next_stage()

    vessel.control.throttle = 1
    time.sleep(1)
    vessel.auto_pilot.target_pitch_and_heading(60, 90)

    while vessel.flight().mean_altitude < 30000:
        time.sleep(1)

    vessel.auto_pilot.target_pitch_and_heading(30, 90)
    time.sleep(1)

    while vessel.resources.amount('LiquidFuel') > 0.1:
        time.sleep(1)

    vessel.control.activate_next_stage()

if __name__ == '__main__':
    run()
