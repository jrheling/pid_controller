#-------------------------------------------------------------------------------
# PID.py
# A simple implementation of a PID controller
#-------------------------------------------------------------------------------
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
# This code is substantially derivative:
#
# Originally based on sample source cdoe from "Real-World Instrumentation with Python"
# by J. M. Hughes, published by O'Reilly Media, December 2010, ISBN 978-0-596-80956-0,
# available at http://examples.oreilly.com/9780596809577/CH09/PID.py.
#
# Heavily modified to add most of the features and fixes described in Brett Beauregard's
# "Improving the Beginner's PID" article (http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/)
#  - All of the improvements described were made with the exception of hardcoding sample
#    time (since invocation in the python context doesn't seem reliably precise enough, 
#    in terms of timing), and controller direction.


import time

class PID(object):
    """ Simple PID control.

        This class implements a simplistic PID control algorithm. When first
        instantiated all the gain variables are set to zero, so calling
        the method gen_out will just return zero.
    """
    
    # pylint: disable=E0202
    #    (pylint 0.25.1 can't handle property assignment from init - see http://www.logilab.org/ticket/89786)
    
    def __init__(self):
        # initialze gains
        self.Kp = 0
        self.Kd = 0
        self.Ki = 0
        
        self.setpoint = 0
        self.out_min = None
        self.out_max = None

        self._last_out = None
        self._manual_mode = False
        self._manual_override_output = None

        self.initialize()

    @property 
    def manual_mode(self):
        return self._manual_mode
    
    @manual_mode.setter
    def manual_mode(self, invar):
        """ Enable/Disable manual mode """
        if invar not in (True, False):
            raise ValueError("non-boolean value can't be assigned to manual_mode")
        if invar is True:
            self._manual_mode = True
        elif invar is False:
            if self._manual_mode is True:         ## turning manual mode off
                self._manual_mode = False
                # need to re-init to avoid confusing the PID state with whatever happened
                #   while in manual mode
                self._prev_tm = time.time()
                self._prev_PV = 0
                self._Ci = 0

    @property
    def Cp(self):
        return self._Cp
    
    @property
    def Ci(self):
        return self._Ci

    @property
    def Cd(self):
        return self._Cd

    def manual_override(self, manout=None):
        """ Try to manually force a specified output level.  Will set _manual_mode implicitly.
        
            Returns: output level actually set, or None if no output level exists
            
            Notes:
            * actual output might be higher or lower than the parameter, if the param was >max or <min
            * if a manual override has been previously set but is not yet the output level (because)
                gen_out() has not yet been called, this will return the manually set level
        """
        if manout is not None:
            if (manout < self.out_min):
                manout = self.out_min
            elif (manout > self.out_max):
                manout = self.out_max
            self.manual_mode = True
            self._manual_override_output = manout
            return manout
        else:
            ## if the PID hasn't been running and we manually set a value (e.g. preparing to
            ##   auto-tune), we'll get here before gen_out() has run to set _last_out to 
            ##   _manual_override_output.  In that case, we return _manual_override_output
            if self._last_out is None:
                return self._manual_override_output
            return self._last_out

    def initialize(self):
        # initialize delta t variables
        self._curr_tm = time.time()
        self._prev_tm = self._curr_tm

        self._prev_PV = 0

        # term result variables
        self._Cp = 0
        self._Ci = 0   # sum of errors
        self._Cd = 0


    def gen_out(self, current_PV):
        """ Performs a PID computation and returns a control value.
        
            This is based on the elapsed time (dt) and the current value of the process variable 
            (i.e. the thing we're measuring and trying to change).
            
        """
        if self._manual_mode is True:
            self._last_out = self._manual_override_output
            return self._last_out
        self._curr_tm = time.time()               # get t
        dt = self._curr_tm - self._prev_tm        # get delta t

        ## working error variables
        error = self.setpoint - current_PV
        self._Ci += self.Ki * (error * dt)      # add current error to accumulated error
                                                # Ki brought in to the integral term to avoid
                                                #  I-term bumps when tuning parameters are
                                                #  changed
                                                # http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-tuning-changes/


        # derivative computation
        #
        # rather than tracking the derivative of the error, we track the derivative of the
        #  process variable (the measured quantity) only, since that will be the same as the
        #  derivative of the error in all cases where the setpoint is unchanged.  Skipping
        #  this when the setpoint changes is a feature, since it avoids spurious D term 
        #  fluctuations ("derivative kick").  
        #
        # see http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-derivative-kick/
        dPV = current_PV - self._prev_PV          
        self._Cd = 0                             # avoid div by zero
        if dt > 0:
            self._Cd = dPV / dt    

        # compute output
        outval = (self.Kp * error) + self._Ci - (self.Kd * self._Cd)
        # constrain Ci to configured limits to avoid 'reset windup' (when the I term 
        #  grows really large as the PV slowly approaches the setpoint)
        #
        # [From comment thread at http://brettbeauregard.com/blog/2011/04/improving-the-beginner%E2%80%99s-pid-reset-windup/]
        if self.out_max is not None:
            if (outval > self.out_max):
                self._Ci -= outval - self.out_max
                outval = self.out_max
        if self.out_min is not None:
            if (outval < self.out_min):
                self._Ci += self.out_min - outval
                outval = self.out_min            
        
        self._Cp = error                         # for external view of PID state
        
        # saved for next time through
        self._prev_tm = self._curr_tm               
        self._prev_PV = current_PV                             

        self._last_out = outval
        return self._last_out
