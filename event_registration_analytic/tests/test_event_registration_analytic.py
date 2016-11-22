# -*- coding: utf-8 -*-
# © 2016 Alfredo de la Fuente - AvanzOSC
# © 2016 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp.addons.sale_order_create_event.tests.\
    test_sale_order_create_event import TestSaleOrderCreateEvent


class TestEventRegistrationAnalytic(TestSaleOrderCreateEvent):

    def setUp(self):
        super(TestEventRegistrationAnalytic, self).setUp()
        self.wiz_confirm_model = self.env['wiz.event.confirm.assistant']
        self.wiz_del_model = self.env['wiz.event.delete.canceled.registration']
        self.wiz_impute_model = self.env['wiz.impute.in.presence.from.session']
        self.claim_model = self.env['crm.claim']
        self.registration_model = self.env['event.registration']
        self.account_model = self.env['account.analytic.account']
        self.wiz_another_model = self.env['wiz.registration.to.another.event']
        self.wiz_append_model = self.env['wiz.event.append.assistant']

    def test_sale_order_create_event(self):
        self.assertEquals(self.sale_order.project_by_task, 'no')
        self.sale_order.action_button_confirm()
        cond = [('sale_order', '=', self.sale_order.id)]
        events = self.event_model.search(cond)
        self.assertNotEqual(
            len(events), 0, 'Sale order without event')
        wiz_vals = {'partner': self.ref('base.res_partner_26')}
        wiz = self.wiz_add_model.with_context(
            active_ids=events.ids).create(wiz_vals)
        wiz.action_append()
        for event in events:
            event._count_teacher_pickings()
            event._count_teacher_moves()
            event.show_all_registrations()
            event.show_teacher_registrations()
            event.show_teacher_pickings()
            event.show_teacher_moves()
            self.assertEquals(event.count_all_registrations,
                              len(event.no_employee_registration_ids) +
                              len(event.employee_registration_ids))
            self.assertEquals(event.count_registrations,
                              len(event.no_employee_registration_ids))
            self.assertEquals(event.count_teacher_registrations,
                              len(event.employee_registration_ids))
            self.assertEquals(
                event.count_registrations + event.count_teacher_registrations,
                len(event.registration_ids))
            registration_vals = ({'event_id': event.id,
                                  'partner_id':
                                  self.env.ref('base.res_partner_25').id,
                                  'state': 'draft',
                                  'date_start': '2025-01-15 08:00:00',
                                  'date_end': '2025-02-28 09:00:00'})
            registration = self.registration_model.create(registration_vals)
            event._compute_seats()
            self.assertEqual(
                event.seats_unconfirmed, 1, 'Draft registrations error')
            wiz_vals = {'name': 'confirm assistants'}
            wiz = self.wiz_confirm_model.create(wiz_vals)
            wiz.with_context(
                {'active_ids': [event.id]}).action_confirm_assistant()
            self.assertNotEqual(
                registration.state, 'draft', 'Registration not confirmed')
            registration._calculate_required_account()
            registration._onchange_partner()
            registration.registration_open()
            self.wiz_impute_model.with_context(
                {'active_ids':
                 [event.track_ids[0].id]}).default_get(['lines'])
            impute_line_vals = {
                'presence': event.track_ids[0].presences[0].id,
                'session': event.track_ids[0].presences[0].session.id,
                'session_date': event.track_ids[0].presences[0].session_date,
                'partner': event.track_ids[0].presences[0].partner.id,
                'notes': 'presence notes',
                'create_claim': True}
            wiz_impute = self.wiz_impute_model.create(
                {'lines': [(0, 0, impute_line_vals)]})
            wiz_impute.button_impute_hours()
            event.registration_ids.write({'state': 'cancel'})
            presences = event.track_ids.mapped('presences')
            presences.write({'state': 'canceled'})
            wiz_del = self.wiz_del_model.create({})
            wiz_del.with_context(
                {'active_ids': [event.id]}).delete_canceled_registration()
            self.assertEqual(len(event.registration_ids), 0,
                             'Event with registrations')

    def test_sale_order_create_event_by_task(self):
        self.assertEquals(self.sale_order.project_by_task, 'no')
        self.sale_order.write({'project_by_task': 'yes'})
        self.sale_order2 = self.sale_order.copy()
        self.sale_order2.project_id = self.sale_order.project_id
        self.sale_order2.action_button_confirm()
        self.sale_order.action_button_confirm()
        cond = [('sale_order', '=', self.sale_order.id)]
        events = self.event_model.search(cond)
        self.assertNotEqual(
            len(events), 0, 'Sale order without event')
        wiz_vals = {'partner': self.ref('base.res_partner_26')}
        wiz = self.wiz_add_model.with_context(
            active_ids=events.ids).create(wiz_vals)
        wiz.action_append()
        for event in events:
            self.assertEquals(event.count_registrations,
                              len(event.no_employee_registration_ids))
            self.assertEquals(event.count_teacher_registrations,
                              len(event.employee_registration_ids))
            self.assertEquals(
                event.count_registrations + event.count_teacher_registrations,
                len(event.registration_ids))
        vals = self.wiz_append_model._prepare_data_for_account_not_employee(
            events[0], events[0].registration_ids[0])
        analytic_account = self.account_model.create(vals)
        registration = events[0].registration_ids[0]
        registration.analytic_account = analytic_account
        registration._prepare_wizard_registration_open_vals()
        cond = [('id', '!=', events[0].id),
                ('sale_order', '!=', False)]
        events = self.event_model.search(cond, limit=1)
        for new_event in events:
            wiz_another_vals = {
                'event_registration_id': registration.id,
                'event_id': registration.event_id.id,
                'new_event_id': new_event.id}
            wiz = self.wiz_another_model.create(wiz_another_vals)
            var_fields = ['new_event_id', 'event_id']
            wiz.with_context(
                {'active_id': registration.id}).default_get(var_fields)
            wiz.with_context(
                {'active_ids':
                 registration.event_id.ids})._change_registration_event()
            dat = self.wiz_append_model._prepare_data_for_account_not_employee(
                new_event, registration)
            self.assertEquals(
                registration.analytic_account.name, dat.get('name', False),
                'Analytic account without new description')
