# -*-  coding: utf-8 -*-
""""""
# -
# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
import logging
import os.path
from SpiffWorkflow import Task
from SpiffWorkflow.bpmn.BpmnWorkflow import BpmnWorkflow
from SpiffWorkflow.bpmn.storage.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.storage.CompactWorkflowSerializer import \
    CompactWorkflowSerializer
from SpiffWorkflow.storage import DictionarySerializer
from tests.SpiffWorkflow.bpmn.PackagerForTests import PackagerForTests


__author__ = "Evren Esat Ozkan"


class BpmnTestEngine(object):
    def __init__(self, process_name, filename='*.bpmn'):
        self.spec = self.load_workflow_spec(filename, process_name)
        self.workflow = BpmnWorkflow(self.spec)

    @staticmethod
    def load_workflow_spec(filename, process_name):
        f = os.path.join(os.path.dirname(__file__), 'workflows', filename)

        return BpmnSerializer().deserialize_workflow_spec(
            PackagerForTests.package_in_memory(process_name, f))

    def get_named_step(self, name):
        tasks = self.workflow.get_tasks(Task.READY)
        while tasks:
            for task in tasks:
                if name == task.task_spec.name:
                    return task
                else:
                    task.complete()
            tasks = self.workflow.get_tasks(Task.READY)



    def do_next_exclusive_step(self, step_name, with_save_load=False,
                               set_attribs=None, choice=None):
        if with_save_load:
            self.save_restore()

        self.workflow.do_engine_steps()
        tasks = self.workflow.get_tasks(Task.READY)
        self._do_single_step(step_name, tasks, set_attribs, choice)

    @staticmethod
    def _is_match(task, step_name_path):

        if not (task.task_spec.name == step_name_path[-1] or
                task.task_spec.description == step_name_path[-1]):
            return False
        for parent_name in step_name_path[:-1]:
            p = task.parent
            found = False
            while p and p != p.parent:
                if p.task_spec.name == parent_name or \
                        p.task_spec.description == parent_name:
                    found = True
                    break
                p = p.parent
            if not found:
                return False
        return True

    def do_next_named_step(self, step_name, with_save_load=False,
                           set_attribs=None, choice=None,
                           only_one_instance=True):
        if with_save_load:
            self.save_restore()
        step_name_path = step_name.split("|")
        self.workflow.do_engine_steps()

        tasks = list([t for t in self.workflow.get_tasks(Task.READY) if
                      self._is_match(t, step_name_path)])

        self._do_single_step(step_name_path[-1], tasks, set_attribs, choice,
                             only_one_instance=only_one_instance)

    @staticmethod
    def _do_single_step(step_name, tasks, set_attribs=None, choice=None,
                        only_one_instance=True):

        if only_one_instance:
            assert len(
                tasks) == 1, 'Did not find one task for \'%s\' (got %d)' % (
                step_name, len(tasks))
        else:
            assert len(
                tasks) > 0, 'Did not find any tasks for \'%s\'' % step_name

        assert tasks[0].task_spec.name == step_name or \
            tasks[0].task_spec.description == step_name, \
            'Expected step %s, got %s (%s)' % (
                step_name, tasks[0].task_spec.description,
                tasks[0].task_spec.name)
        if not set_attribs:
            set_attribs = {}

        if choice:
            set_attribs['choice'] = choice

        if set_attribs:
            tasks[0].set_data(**set_attribs)
        tasks[0].complete()

    def full_restore(self, state):
        return BpmnWorkflow.deserialize(DictionarySerializer(), state)

    def _get_full_workflow_state(self):
        # self.workflow.do_engine_steps()
        self.workflow.refresh_waiting_tasks()
        return self.workflow.serialize(serializer=DictionarySerializer())

    def full_save_restore(self):
        state = self._get_full_workflow_state()
        logging.debug('Saving state: %s', state)
        before_dump = self.workflow.get_dump()
        self.full_restore(state)
        # We should still have the same state:
        after_dump = self.workflow.get_dump()
        after_state = self._get_full_workflow_state()
        if state != after_state:
            logging.debug("Before save:\n%s", before_dump)
            logging.debug("After save:\n%s", after_dump)
        assert state == after_state

    def save_restore(self):
        state = self._get_workflow_state()
        logging.debug('Saving state: %s', state)
        before_dump = self.workflow.get_dump()
        self.restore(state)
        # We should still have the same state:
        after_dump = self.workflow.get_dump()
        after_state = self._get_workflow_state()
        if state != after_state:
            logging.debug("Before save:\n%s", before_dump)
            logging.debug("After save:\n%s", after_dump)
        assert state == after_state

    def restore(self, state):
        self.workflow = CompactWorkflowSerializer().deserialize_workflow(
            state, workflow_spec=self.spec)

    def get_read_only_workflow(self):
        state = self._get_workflow_state()
        return CompactWorkflowSerializer().deserialize_workflow(
            state, workflow_spec=self.spec, read_only=True)

    def _get_workflow_state(self):
        # self.workflow.do_engine_steps()
        self.workflow.refresh_waiting_tasks()
        return CompactWorkflowSerializer().serialize_workflow(
            self.workflow, include_spec=False)
