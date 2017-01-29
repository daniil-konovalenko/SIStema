# -*- coding: utf-8 -*-

"""Tests for poldnev.models.HistoryEntry."""

import unittest

import django.test

# TODO(Artem Tabolin): find a way not to depend on location of poldnev module
import modules.poldnev.models as models


class HistoryEntryTestCase(django.test.TestCase):
    def setUp(self):
        self.session = models.Session.objects.create(
            poldnev_id='0871',
            name='2008.Кострома')

        self.role = models.Role.objects.create(
            session=self.session,
            poldnev_role='C3.преп')

        self.person = models.Person.objects.create(
            poldnev_id='1',
            first_name='Виктор',
            middle_name='Александрович',
            last_name='Матюхин')

        self.history_entry = models.HistoryEntry.objects.create(
            person=self.person,
            role=self.role)

    def test_str(self):
        """History entry's string representation should be correct."""
        self.assertEqual(
            str(self.history_entry),
            'Виктор Александрович Матюхин (2008.Кострома: C3.преп)')