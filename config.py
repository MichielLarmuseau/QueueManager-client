# -*- coding: utf-8 -*-
import os
vasp = 'vasp'

if os.getenv('VSC_INSTITUTE_CLUSTER') == 'breniac':
    vasp = 'vasp_std'