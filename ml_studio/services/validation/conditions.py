# =========================================================================== #
# Project: ML Studio                                                          #
# Version: 0.1.14                                                             #
# File: \conditions.py                                                        #
# Python Version: 3.7.3                                                       #
# ---------------                                                             #
# Author: John James                                                          #
# Company: Decision Scients                                                   #
# Email: jjames@decisionscients.com                                           #
# ---------------                                                             #
# Create Date: Saturday December 28th 2019, 6:31:33 am                        #
# Last Modified: Sunday December 29th 2019, 1:30:56 pm                        #
# Modified By: John James (jjames@decisionscients.com)                        #
# ---------------                                                             #
# License: Modified BSD                                                       #
# Copyright (c) 2019 Decision Scients                                         #
# =========================================================================== #
"""Classes that manage conditions which are applied to Rule objects.

This module contains the following classes:

    * BaseCondition : The component interface for all Condition classes.
    * ConditionSet : A collection of conditions.
    * Condition : Defines a unique condition.

"""
from abc import ABC, abstractmethod, abstractproperty
from collections import OrderedDict, abc 
import copy
from datetime import datetime
import getpass
import os
import re
import sys
import time
from uuid import uuid4

import numpy as np
import pandas as pd

from ml_studio.services.validation.utils import is_array, is_homogeneous_array
from ml_studio.services.validation.utils import is_simple_array, is_none
from ml_studio.services.validation.utils import is_not_none, is_empty
from ml_studio.services.validation.utils import is_not_empty, is_bool
from ml_studio.services.validation.utils import is_integer, is_number
from ml_studio.services.validation.utils import is_string, is_less
from ml_studio.services.validation.utils import is_less_equal, is_greater
from ml_studio.services.validation.utils import is_greater_equal, is_match
from ml_studio.services.validation.utils import is_equal, is_not_equal
# --------------------------------------------------------------------------- #
#                                 BASECONDITION                               #
# --------------------------------------------------------------------------- #
SYNTACTIC_EVAL_FUNCTIONS = [is_array,is_homogeneous_array,is_simple_array,
                            is_none, is_not_none, is_empty, is_not_empty,
                            is_bool, is_integer, is_number, is_string]

class BaseCondition(ABC):
    """Abstract base class for all Condition classes."""
    
    def __init__(self):
        # Designate unique/opaque userid and other metadata        
        self._id = str(uuid4())
        self._created = datetime.now()
        self._creator = getpass.getuser()

        # Initialize state instance variables
        self._is_valid = True
        self._evaluated_instance = None
        self._evaluated_attribute = None
        
    @property
    def _is_composite(self):
        return False

    # ----------------------------------------------------------------------- #
    #                          Property Management                            #
    # ----------------------------------------------------------------------- #
    @property
    def id(self):        
        return copy.deepcopy(self._id)   

    @property
    def is_valid(self):
        return self._is_valid

    def on(self, value):
        self._evaluated_instance = value
        return self

    def attribute(self, value):
        """Updates current instance and propogates through children."""        
        if hasattr(self._evaluated_instance, value):
            self._evaluated_attribute = value
        else:            
            print("{attr} is not a valid attribute for the {classname} class.".format(
                attr=value, classname=self._evaluated_instance.__class__.__name__
            ))                
        return self  

    @property
    def evaluated_instance(self):
        return copy.deepcopy(self._evaluated_instance)

    @property
    def evaluated_attribute(self):
        return copy.deepcopy(self._evaluated_attribute)

    # ----------------------------------------------------------------------- #
    #                            Composite Management                         #
    # ----------------------------------------------------------------------- #

    def get_condition(self, condition):        
        pass   

    def add_condition(self, condition):           
        pass

    def remove_condition(self, condition):
        pass

    # ----------------------------------------------------------------------- #
    #                                 Operation                               #
    # ----------------------------------------------------------------------- #     
    @abstractmethod
    def evaluate(self):
        pass

    # ----------------------------------------------------------------------- #
    #                              Print Management                           #
    # ----------------------------------------------------------------------- #   
    @property
    def print_condition_set(self):
        pass


# --------------------------------------------------------------------------- #
#                                CONDITIONSET                                 #
# --------------------------------------------------------------------------- #    
class ConditionSet(BaseCondition):
    """A ConditionSet contains Conditions and a logical operator for evaluation.
    
    This is the composite class collects Conditions objects into CollectionSets.
    CollectionSets may contain individual Conditions as well as Condition Sets
    ConditionSets have a logical operator which specifies how the Conditions
    within the set will be evaluated.
    """

    def __init__(self):
        super(ConditionSet, self).__init__()
        self._logical = 'all'
        self._conditions = OrderedDict()

    def reset(self):
        self._conditions = OrderedDict()

    @property
    def _is_composite(self):
        return True

    # ----------------------------------------------------------------------- #
    #                            Composite Management                         #
    # ----------------------------------------------------------------------- #

    def get_condition(self, condition=None):        
        if condition is None:
            return self._conditions
        else:
            return self._conditions[condition.id]   

    def add_condition(self, condition):           
        self._conditions[condition.id] = condition 
        return self

    def remove_condition(self, condition):
        del self._conditions[condition.id]
        return self

    # ----------------------------------------------------------------------- #
    #                            Property Management                          #
    # ----------------------------------------------------------------------- #
    @property
    def logical(self):
        return copy.deepcopy(self._logical)
        
    @property
    def when_all_conditions_are_true(self):
        self._logical = "all"
        return self

    @property
    def when_any_condition_is_true(self):
        self._logical = "any"
        return self        

    @property
    def when_no_conditions_are_true(self):
        self._logical = "none"
        return self        

    def on(self, value):
        """Updates current instance and propogates through children."""
        self._evaluated_instance = value
        if isinstance(self, ConditionSet):                    
            for _, condition in self._conditions.items():
                condition.on(value)                
        else:
            condition._evaluated_instance = value                        
        return self

    def attribute(self, value):
        """Updates current instance and propogates through children."""        
        
        if hasattr(self._evaluated_instance, value):
            self._evaluated_attribute = value
        else:            
            print("{attr} is not a valid attribute for the {classname} class.".format(
                attr=value, classname=self._evaluated_instance.__class__.__name__
            ))                
        if isinstance(self, ConditionSet):
            for _, condition in self._conditions.items():
                condition.attribute(value)                
        else:
            condition._evaluated_attribute = value                        
        return self        

    # ----------------------------------------------------------------------- #
    #                                Operation                                #
    # ----------------------------------------------------------------------- #
    @property
    def evaluate(self):        

        # Update list of conditions with evaluations
        ({self.add_condition(condition.evaluate) for (_, condition) in self._conditions.items()})
    
        # Obtain evaluation results from each condition in the list
        is_valid = [condition.is_valid for (_,condition) in self._conditions.items()]

        # Execute appropriate logical
        if self._logical == "all":
            self._is_valid = all(is_valid)
        elif self._logical == "any":
            self._is_valid = any(is_valid)
        else:
            self._is_valid = not any(is_valid)

        return self

    # ----------------------------------------------------------------------- #
    #                             Print Management                            #
    # ----------------------------------------------------------------------- #
    @property
    def print_condition_set(self):
        if self._is_composite:
            print("\nCondition Set: {id} evaluates to true when {logical} \
                conditions pass.".format(
                id=self._id, 
                logical=self._logical
            ))
            for _,v in self._conditions.items():
                if v._is_composite:
                    v.print_condition_set
                else:
                    v.print_condition  
        return self

# --------------------------------------------------------------------------- #
#                                 CONDITION                                   #
# --------------------------------------------------------------------------- #           
class Condition(BaseCondition):
    """Class that defines a condition to apply to Rule objects."""

    def __init__(self):
        super(Condition, self).__init__()
        self._a = None
        self._b = None
        self._a_attribute = None
        self._b_attribute = None                
        self._eval_function = None
        self._is_valid = "Not evaluated."

    def _reset(self):
        self._is_valid = "Not evaluated."
    
    @property
    def _is_composite(self):
        return False
    
    def when(self, value):
        self._a = value
        return self

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, value):
        self._b = value

    @property
    def is_none(self):
        self._eval_function = is_none
        return self

    @property
    def is_not_none(self):
        self._eval_function = is_not_none
        return self

    @property
    def is_empty(self):
        self._eval_function = is_empty        
        return self
    
    @property
    def is_not_empty(self):
        self._eval_function = is_not_empty         
        return self

    @property
    def is_bool(self):
        self._eval_function = is_bool        
        return self
    
    @property
    def is_integer(self):
        self._eval_function = is_integer          
        return self

    @property
    def is_number(self):
        self._eval_function = is_number
        return self

    @property
    def is_string(self):
        self._eval_function = is_string         
        return self

    def is_equal(self, b):
        self._b = b
        self._eval_function = is_equal
        return self

    def is_not_equal(self, b):
        self._b = b
        self._eval_function = is_not_equal        
        return self

    def is_less(self, b):
        self._b = b
        self._eval_function = is_less
        return self

    def is_less_equal(self, b):
        self._b = b
        self._eval_function = is_less_equal        
        return self

    def is_greater(self, b):
        self._b = b
        self._eval_function = is_greater
        return self

    def is_greater_equal(self, b):
        self._b = b
        self._eval_function = is_greater_equal        
        return self

    def is_match(self, b):
        self._b = b
        self._eval_function = is_match
        return self
    
    
    def _get_value(self,a):
        if isinstance(a, str):
            try:
                value = getattr(self._evaluated_instance, a)
            except AttributeError:        
                value = a
        else:
            value = a
        return value
        
    @property
    def evaluate(self):        
        self._reset()
        self._a = self._get_value(self._a)
        self._b = self._get_value(self._b)
        self._is_valid = self._eval_function(self._a, self._b)        
        return self
        
    @property
    def _print_syntactic_condition(self):

        print("\n   Condition #{id}: when {a} is {func} evaluates to {is_valid}."\
            .format(
                id=self._id, 
                a=self._a,
                func=self._eval_function, 
                is_valid=self._is_valid
            ))
    
    @property
    def _print_semantic_condition(self):
            
        print("\n   Condition #{id}: when {a} is {func} {b} evaluates to {is_valid}."\
            .format(
                id=self._id, 
                a=self._a,
                func=self._eval_function, 
                b=self._b,
                is_valid=self._is_valid
            ))
    @property
    def print_condition(self):
        """Prints condition for most recent result or current values."""

        if self._eval_function in SYNTACTIC_EVAL_FUNCTIONS:
            self._print_syntactic_condition
        else:
            self._print_semantic_condition
