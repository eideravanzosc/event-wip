# -*- coding: utf-8 -*-
# (c) 2025 Alfredo de la Fuente - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import openerp.tests.common as common


class TestEventRegistrationAnalytic(common.TransactionCase):

    def setUp(self):
        super(TestEventRegistrationAnalytic, self).setUp()
        self.task_model = self.env['project.task']
        self.sale_model = self.env['sale.order']
        self.account_model = self.env['account.analytic.account']
        self.project_model = self.env['project.project']
        self.event_model = self.env['event.event']
        self.task_model = self.env['project.task']
        self.procurement_model = self.env['procurement.order']
        self.wiz_add_model = self.env['wiz.event.append.assistant']
        self.registration_model = self.env['event.registration']
        account_vals = {'name': 'account procurement service project',
                        'date_start': '2025-01-15',
                        'date': '2025-02-28'}
        self.account = self.account_model.create(account_vals)
        project_vals = {'name': 'project 1',
                        'analytic_account_id': self.account.id}
        self.project = self.project_model.create(project_vals)
        service_product = self.env.ref('product.product_product_consultant')
        service_product.write({'performance': 5.0,
                               'recurring_service': True})
        service_product.performance = 5.0
        service_product.route_ids = [
            (6, 0,
             [self.ref('procurement_service_project.route_serv_project')])]
        sale_vals = {
            'name': 'sale order 1',
            'partner_id': self.ref('base.res_partner_1'),
            'partner_shipping_id': self.ref('base.res_partner_1'),
            'partner_invoice_id': self.ref('base.res_partner_1'),
            'pricelist_id': self.env.ref('product.list0').id,
            'project_id': self.account.id,
            'project_by_task': 'no'}
        sale_line_vals = {
            'partner_id': self.ref('base.res_partner_1'),
            'product_id': service_product.id,
            'name': service_product.name,
            'product_uom_qty': 7,
            'product_uos_qty': 7,
            'product_uom': service_product.uom_id.id,
            'price_unit': service_product.list_price,
            'performance': 5.0,
            'january': True,
            'february': True,
            'week4': True,
            'week5': True,
            'tuesday': True,
            'thursday': True,
            'start_date': '2025-01-15',
            'start_hour': 8.00,
            'end_date': '2025-02-28',
            'end_hour': 12.00}
        sale_vals['order_line'] = [(0, 0, sale_line_vals)]
        self.sale_order = self.sale_model.create(sale_vals)
        account_vals = {'name': 'account procurement service project',
                        'date_start': '2025-01-15',
                        'date': '2025-02-28'}
        self.account2 = self.account_model.create(account_vals)
        project_vals = {'name': 'project 1',
                        'analytic_account_id': self.account2.id}
        self.project2 = self.project_model.create(project_vals)
        service_product = self.env.ref('product.product_product_consultant')
        service_product.write({'performance': 5.0,
                               'recurring_service': True})
        service_product.performance = 5.0
        service_product.route_ids = [
            (6, 0,
             [self.ref('procurement_service_project.route_serv_project')])]
        sale_vals = {
            'name': 'sale order 2',
            'partner_id': self.ref('base.res_partner_1'),
            'partner_shipping_id': self.ref('base.res_partner_1'),
            'partner_invoice_id': self.ref('base.res_partner_1'),
            'pricelist_id': self.env.ref('product.list0').id,
            'project_id': self.account2.id,
            'project_by_task': 'yes'}
        sale_line_vals = {
            'partner_id': self.ref('base.res_partner_1'),
            'product_id': service_product.id,
            'name': service_product.name,
            'product_uom_qty': 7,
            'product_uos_qty': 7,
            'product_uom': service_product.uom_id.id,
            'price_unit': service_product.list_price,
            'performance': 5.0,
            'january': True,
            'february': True,
            'week4': True,
            'week5': True,
            'tuesday': True,
            'thursday': True,
            'start_date': '2025-01-15',
            'start_hour': 8.00,
            'end_date': '2025-02-28',
            'end_hour': 12.00}
        sale_vals['order_line'] = [(0, 0, sale_line_vals)]
        self.sale_order2 = self.sale_model.create(sale_vals)

    def test_sale_order_create_event(self):
        self.sale_order.action_button_confirm()
        cond = [('project_id', '=', self.project.id)]
        event = self.event_model.search(cond, limit=1)
        self.assertNotEqual(
            len([event]), 0, 'Sale order withour event')
        wiz_vals = {'min_event': event.id,
                    'max_event': event.id,
                    'min_from_date': '2025-01-15 00:00:00',
                    'max_to_date': '2025-02-28 00:00:00',
                    'from_date': '2025-01-15 00:00:00',
                    'to_date': '2025-02-28 00:00:00',
                    'partner': self.env.ref('base.res_partner_26').id}
        wiz = self.wiz_add_model.with_context(
            {'active_ids': [event.id]}).create(wiz_vals)
        wiz.onchange_partner()
        wiz.with_context({'active_ids': [event.id]}).action_append()
        event._count_registrations()
        event._count_teacher_registrations()
        event._count_teacher_pickings()
        event._count_teacher_moves()
        event.show_teacher_registrations()
        event.show_teacher_pickings()
        event.show_teacher_moves()
        for registration in event.registration_ids:
            registration._calculate_required_account()
        for track in event.track_ids:
            track._calc_real_duration()
        event.write({'no_employee_registration_ids': [[2, 3, False]],
                     'employee_registration_ids': [[2, 3, False]]})
