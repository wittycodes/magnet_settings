# -*- coding: utf-8 -*-
"""
spectrometer_quadrupole.py

This script controls the quadrupole magnets that is part of the electron spectrometer in the AWAKE experiment 
at CERN. Developed by James Chappell: james.anthony.chappell@cern.ch
"""

import pyjapc
import numpy as np
import matplotlib.pyplot as plt
from time import sleep
import argparse

japc = pyjapc.PyJapc('SPS.USER.ALL')
japc.rbacLogin(username='awakeop', password='')
japc.rbacGetToken()

def quadrupole_turn_on(current):
    
    """ 
    This function turns on the UCL AWAKE Spectrometer dipole to the settings 
    given by the input arguments.
    
    Arguments:
        
        - current           This is the value of the current that the quadrupole 
                            should be set to. It is measured in Amps [A].
                    
                            
    """
    
    # Check whether PC mode is off
    
    print("Turning on quadrupole to current {}A.\n".format(current))
    print("Checking PC state...")
    
    pc_status = japc.getParam('RPADA.BB4.RQNI.412432/STATE')
    
    if pc_status['PC'] != 'OFF':
        
        japc.setParam('RPADA.BB4.RQNI.412432/MODE.PC', 'OFF')
        
        print("PC was in state: {}".format(pc_status['PC']))
        print("Turning PC off.")
        
        # Wait a few seconds to allow PC to switch off
        sleep(10)
        
        updated_status = japc.getParam('RPADA.BB4.RQNI.412432/STATE')
        
        print("PC is now in state: {}\n".format(updated_status['PC']))
        print("Beginning quadrupole turn on procedure...\n")
        
    else:
        
        print("PC already in state: {}\n".format(pc_status['PC']))
        print("Beginning quadrupole turn on procedure...\n")
        
        
    # Update PC modes and check in correct state
    
    print("Updating PC modes...")
    
    japc.setParam('RPADA.BB4.RQNI.412432/MODE.PC', 'ON_STANDBY')
    sleep(10)
    japc.setParam('RPADA.BB4.RQNI.412432/MODE.PC', 'IDLE')
    
    pc_status = japc.getParam('RPADA.BB4.RQNI.412432/STATE')
    
    print("PC in state: {}\n".format(pc_status['PC']))
    
    # Set the trim settings for duration and final according to the input
    # arguments specified.
    
    sleep(5)
    
    current_set = float(current)
    
    print("Setting magnet PLEP settings to:")
    print("Current = {}A\n".format(current_set))
    
    japc.setParam('RPADA.BB4.RQNI.412432/REF.PLEP.FINAL', current_set)
    
    sleep(3)
    
    check_current = japc.getParam('RPADA.BB4.RQNI.412432/REF.PLEP.FINAL')
    
    print("Magnet settings have been set to:")
    print("Current = {}A".format(check_current))
    
    # Finding _non_multiplexed_sps context
    
    print("Setting function type...")
    
    japc.setParam('RPADA.BB4.RQNI.412432/REF.FUNC.TYPE', 'PLEP')
    sleep(1)
    func_type = japc.getParam('RPADA.BB4.RQNI.412432/REF.FUNC.TYPE')
    
    print("Function type set to: {}\n".format(func_type))
    
    # PC state should now be 'ARMED'. 
    
    check_state = japc.getParam('RPADA.BB4.RQNI.412432/STATE')
    
    print("PC State set to: {}\n".format(check_state['PC']))
    
    if check_state['PC'] == 'ARMED':
    
        print("Turning on quadrupole...\n")
    
        japc.setParam('RPADA.BB4.RQNI.412432/REF.RUN', 1.0)
        
        sleep(1)
        
        check_run_state = japc.getParam('RPADA.BB4.RQNI.412432/STATE')
        
        print("PC State: {}".format(check_run_state['PC']))
    
    else:
        
        print("PC state not 'ARMED'. Breaking...")
        return 0
    
    # Wait for ramp duration to check what the current is.
    
    sleep(3)
    
    current_test = japc.getParam('RPADA.BB4.RQNI.412432/MEAS.I')
    
    print("Current is at {}A".format(current_test))
    
    
def current_plot():
    
    """
    This function plots the current values for the last 10 seconds, and also returns the mean current.
    """
    
    print("\nGathering current data. Please wait...\n")
    
    timesteps = 1
    
    current_array = []
    
    while timesteps <= 100:
        
        current_val = japc.getParam('RPADA.BB4.RQNI.412432/MEAS.I')
        current_array.append(current_val)
        sleep(0.1)
        timesteps = timesteps + 1
    
    mean_val = np.mean(current_array)
    
    print("Mean current is {0:3.3f}A".format(mean_val))
    x = np.linspace(0, 10, 100)
    plt.plot(x, current_array, "-o")
    plt.plot((0, 100), (mean_val, mean_val), 'r-', linewidth=1.5)
    plt.xlabel("Time [s]")
    plt.ylabel("Current [A]")
    plt.xlim(0, 10)
    plt.ylim(mean_val - 2, mean_val + 2)
    plt.show()
    

def quadrupole_turn_off():
    
    """
    This function checks the state of the dipole, and turns it off if it isn't already.
    """
    
    check_state = japc.getParam('RPADA.BB4.RQNI.412432/STATE')
    
    if check_state['PC'] == 'OFF':
        
        print("PC current state: {}".format(check_state['PC']))
        print("PC is already off. Do not need to turn off.")
        return
    
    else:
        
        print("PC current state: {}".format(check_state['PC']))
        print('Turning off...')
        japc.setParam('RPADA.BB4.RQNI.412432/MODE.PC', 'OFF')
        
        # Allow time to shutdown
        
        sleep(5)
        
        pc_state = japc.getParam('RPADA.BB4.RQNI.412432/STATE')
        
        print("PC current state: {}".format(pc_state['PC']))
    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="""
    This script controls the quadrupole magnet that is part of the electron spectrometer in the AWAKE experiment at CERN.
    """, formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument('--mode', dest='mode', default=None, choices=['on', 'off',
    'plot'],  help='''
    This defines what you would like to do to the quadrupole magnet. The options 
    are:
        
        - 'on'      Switches on the magnet to the current value given as an input argument.
        
        - 'off'     Switches off the magnet.
        
        - 'plot'    Produces a plot of the current values over the past 10 seconds.
    ''')
        
    parser.add_argument('--current', dest='current', default=None, help='''
    This argument defines the value of the current that the dipole magnet should be set to. It is measured in Amps [A].''')
    
    arguments = parser.parse_args()
    
    mode = arguments.mode
    
    if mode == 'off':
        
        quadrupole_turn_off()
        
    elif mode == 'plot':
        
        current_plot()
        
    elif arguments.mode == 'on' and arguments.current is None:
        
        parser.error("--mode 'on' also requires --current option. See --help for more details.")
        
    else:
        
        current_set = float(arguments.current)
        
        quadrupole_turn_on(current_set)
        
        
