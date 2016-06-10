# -*- coding: utf-8 -*-
from __future__ import division
# Copyright (C) 2012 Matthew Hampton
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from SpiffWorkflow.bpmn.specs.BpmnSpecMixin import BpmnSpecMixin
from SpiffWorkflow.specs.Simple import Simple


class ServiceTask(Simple, BpmnSpecMixin):
    """
    Task Spec for a bpmn:serviceTask node.
    """

    def __init__(self, parent, name, service_class, expression, result_variable,  type, topic, **kwargs):
        """
        Constructor.

        :param script: the script that must be executed by the script engine.
        """
        self.service_class = service_class
        self.expression = expression
        self.type = type
        self.topic = topic
        self.result_variable = result_variable
        super(ServiceTask, self).__init__(parent, name, **kwargs)


    def _on_complete_hook(self, task):
        if task.workflow._is_busy_with_restore():
            return
        assert not task.workflow.read_only
        super(ServiceTask, self)._on_complete_hook(task)
