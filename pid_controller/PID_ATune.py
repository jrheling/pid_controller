#!/usr/bin/python

# PID_ATune.py
#
# Copyright 2014 Joshua Heling <jrh@netfluvia.org>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
# This is a Python port of Brett Beauregard's Arduino PID Autotune Library
#    (https://github.com/br3ttb/Arduino-PID-AutoTune-Library)
#


import time
import PeakCounter

# TODOs (FIXME)
# * fix docstring

class ControlType:
    PI, PID = range(2)

class PIDNotStableError(Exception):
    def __init__(self, arg):
        self.msg = arg

class PID_ATune(object):
    """ PID Autotune mechanism
    
        Based on method described at http://brettbeauregard.com/blog/2012/01/arduino-pid-autotune-library/
        
        takes:
          measure_func - function that will return a float indicating the current value 
                          of the Process Variable (value influenced by the PID)
    """

    # pylint: disable=E0202
    #    (pylint 0.25.1 can't handle property assignment from init - see http://www.logilab.org/ticket/89786)

    def __init__(self, measure_func, output_func):
        ## IMPROVE: there's a better way to pass these args.  Maybe a base class?
        # measure_func must take nothing and return the current PV
        self._measure_func = measure_func
        # if given a non-None parameter, output_func will try to set the output to that 
        # output_func always returns the current output level (after changing it, if a parameter was passed)
        self._output_func = output_func
        
        ## configure
        """ Set how far above and below the starting value the output will step. """
        self.output_step = 200   ## ? sanity-check value (IMPROVE: - make configurable?)
        """ Determine if we're autotuning a PID controller or a PI controller. """
        self.control_type = ControlType.PID
        """ Ignore signal chatter smaller than this. """
        self.noise_band = None
        self.lookback_sec = 10
        self.noise_band = 0.5

        self._max_peaks = 9

        self.PC = PeakCounter.PeakCounter(self._max_peaks)

        self._last_time = time.time()

    @property
    def control_type(self):
        return self.__control_type

    @control_type.setter
    def control_type(self, ct):
        if ct not in (ControlType.PI, ControlType.PID):
            raise TypeError("control_type takes a boolean")
        self.__control_type = ct

    @property
    def lookback_sec(self):
        return int(self._num_lookback_samples * self._sample_time)
            
    @lookback_sec.setter
    def lookback_sec(self, sec):
        if sec < 1:
            sec = 1
        
        if sec < 25:
            self._num_lookback_samples = sec * 4
            self._sample_time = (250 / 1000.0)
        else:
            self._num_lookback_samples = 100
            self._sample_time = (sec * 10) / 1000.0
        
    def _finish_up(self):
        """ Generate tuning parameters. """
        # put things back where we found them
        self._change_output(self._output_start)
        
        self._Ku = 4 * (2 * self.output_step) / ((self.abs_max - self.abs_min) * 3.14159)
        self._Pu = self.PC.last_peak_delta 
    
    def _change_output(self, newout):
        self._output = self._output_func(newout)
        return self._output
    
    def verify_stability(self):
        """ Test if the input/output of the attached PID are stable. 
        
            Raises PIDNotStableError if instability is detected.  Returns True if stable.
        """
        accuracy = 0.005 ## allow 0.5% variance to still count as "stable" (IMPROVE: - make configurable?)
        print "in verify_stability()"
        output = self._change_output(None)
        print "output is %f " % output
        input = self._measure_func()
        print "input is %f" % input
        last_check = time.time()
        for delay in (0.01, 0.1, 1.0, 10, 100):  
            now = time.time()
            #print "delaying for %f s" % delay
            while (last_check + delay > now):
                time.sleep((last_check + delay) - now)  # finish sleeping if we got interrupted
                now = time.time()

            #print "done sleeping"
            curr_in = self._measure_func()

            if (abs(curr_in - input)/input > accuracy):
                raise PIDNotStableError("Measured value was %f, expected %f (after %fs)" % (curr_in, input, delay))
            curr_out = self._change_output(None)
            if (curr_out != output):
                raise PIDNotStableError("Output level changing.  Expected %d, got %d (after %fs)" % (output, curr_out, delay))

        print "we're stable!"
        return True
    
    def Tune(self):
        """ Run autotune logic, based on configured parameters.  Returns param tuple when complete. """

        ## FIXME what about the scenario where it doesn't complete? We should have some abort/timeout/give up scenario
            ## need some informed idea of how long this might take before that's possible
        
        self.verify_stability()
        
        last_run = 0
        self.abs_max = self.abs_min = self.setpoint = self._measure_func()

        self._output_start = self._change_output(None)
        self._change_output(self._output + self.output_step)
        
        while (True):
            if self.PC.num_peaks > self._max_peaks:
                return self._finish_up()      

            # don't run main Tune loop more often than sampleTime, but also account for other interrupts
            #   that might disrupt sleep
            now = time.time()
            while (now <= last_run + self._sample_time):
                time.sleep(0.01)
                now = time.time()
            last_run = now
            
            # measure
            ref_val = self._measure_func()
            
            # update max/min
            if ref_val > self.abs_max:
                self.abs_max = ref_val
            elif ref_val < self.abs_min:
                self.abs_min = ref_val

            ## oscillate output based on the current PV's relation to the setpoint
            if ref_val > (self.setpoint + self.noise_band):
                self._change_output(self._output - self.output_step)
            elif ref_val < (self.setpoint - self.noise_band):
                self._change_output(self._output + self.output_step)
            
            # look for peaks
            self.PC.add_value(ref_val)

            # see if we have enough peaks         
            if self.PC.just_inflected and (self.PC.num_peaks > 2):
                # see if it's possible to autotune based on the last peaks
                pks = self.PC.get_last_peaks(3)
                avg_separation = (abs(pks[2] - pks[1]) + abs(pks[1] - pks[0]))/2
                if avg_separation < 0.05 * (self.abs_max - self.abs_min):
                    return self._finish_up()
    
    @property
    def Kp(self):
        if self.control_type == ControlType.PID:
            return 0.6 * self._Ku
        else:
            return 0.4 * self._Ku

    @property    
    def Ki(self):
        # Ki = Kc / Ti
        if self.control_type == ControlType.PID:
            return 1.2 * self._Ku / self._Pu
        else:
            return 0.48 * self._Ku / self._Pu

    @property    
    def Kd(self):
        # Kd = Kc * Td
        if self.control_type == ControlType.PID:
            return 0.075 * self._Ku * self._Pu
        else:
            return 0
    
    
    