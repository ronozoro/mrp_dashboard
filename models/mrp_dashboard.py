import json
from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date

from odoo import models, api, _, fields
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang
import random


class ManufacturingDashboard(models.Model):

    _name = 'manufacturing.dashboard'

    @api.multi
    def work_order(self,name):
        refreshed_data2 = self.env['mrp.production'].search([('state', 'not in', ('cancel', 'done')), ('company_id', '=', self.company_id.id),('name','=',name)])
        for nam in refreshed_data2:
            mo_work_orders = self.env['mrp.workorder'].search([('production_id', '=', refreshed_data2.id), ('company_id', '=', self.company_id.id)])
            if mo_work_orders:
                work_order_name = []
                for val in mo_work_orders:
                    work_order_name.append(val.name)

                return work_order_name

    @api.one
    def _mo_details(self):
        pass
        self.mo_details = json.dumps(self.get_mo_details())
        print("the values in the mo_details")

    @api.one
    def _work_order_details(self):
        self.wo_details = json.dumps(self.work_order_per_mo())

    name = fields.Char(string='name')
    mo_data = fields.Many2one('mrp.production', string='Manufacturing Order')
    wo_data = fields.Many2one('mrp.workorder', string='Workorder Data')
    wo_details = fields.Text(compute='_work_order_details')
    mo_details = fields.Text(compute='_mo_details')
    color = fields.Integer("Color Index", default=0)
    company_id = fields.Many2one('res.company', 'Company')

    def get_mo_details(self):
        data_list = []
        if self.mo_data :
            mo = self.mo_data
            print("values in mo",mo)
            for i in mo:
                mo_work_orders = self.env['mrp.workorder'].search([('production_id', '=', i.id), ('company_id', '=', self.company_id.id)])
                print("the work order is",mo_work_orders)
                if mo_work_orders:
                    work_order_names = []
                    # work_order_names = ''
                    data = {}
                    for wo in mo_work_orders:
                        work_order_names.append(wo.name)
                        # work_order_names+=wo.name+"      "
                    data.update({
                        'id': i.id,
                        'name': i.name,
                        'product_id': i.product_id.name,
                        'product_quantity': i.product_qty,
                        'wo_names': work_order_names
                    })
                    data_list.append(data)
        print("the data in data_list is",data_list)
        return data_list

    def get_wo_details(self):
       query = """ select a.id, a.name,a.state,a.production_id from mrp_workorder as a,mrp_production b where
                a.production_id= b.id and b.state not in ('cancel','done') and a.company_id = b.company_id """
       self.env.cr.execute(query)
       wo = self.env.cr.fetchall()
       return wo

    def func_open_action(self):
        print("the value in the self",self.mo_data.id,self)
        result = {}
        model = 'mrp.production'
        action = self.env["ir.actions.act_window"].search([("res_model", "=", model)])
        res = self.env["ir.ui.view"].search([("model", "=", model), ("type", "in", ("list", "tree"))])[0].id
        res_form = self.env["ir.ui.view"].search([("model", "=", model), ("type", "=", "form")])[0].id
        result = action[0].read()[0]
        result['views'] = [(res, 'list'), (res_form, 'form')]

        # result['domain'] = [('workcenter_id', '=', self.work_center_name.id), ("state", '=', 'progress')]
        result['res_id'] = self.mo_data.id
        result['domain'] = [('id', '=',self.mo_data.id)]
        result['target'] = 'current'
        print ("the value in the result",result)
        return result

    def action_by_bar_graph_for_work_order(self):
        result = {}
        model = 'mrp.workorder'
        action = self.env["ir.actions.act_window"].search([("res_model", "=", model)])
        res = self.env["ir.ui.view"].search([("model", "=", model), ("type", "in", ("list", "tree"))])[0].id
        res_form = self.env["ir.ui.view"].search([("model", "=", model), ("type", "=", "form")])[0].id
        result = action[0].read()[0]
        result['views'] = [(res, 'list'), (res_form, 'form')]

        # result['domain'] = [('workcenter_id', '=', self.work_center_name.id), ("state", '=', 'progress')]
        result['target'] = self.id
        # result['target'] = 'main'
        return result


    '''Bar Chart data function not for multichartbar'''
    @api.multi
    def get_bar_graph_datas(self):
        data_list = []
        query = """select id,name,product_id,product_qty from mrp_production where state not in ('cancel','done') and 
                                                               company_id = '%s' """ % (self.company_id.id)
        self.env.cr.execute(query)
        mo = self.env.cr.fetchall()
        print("values in mo", mo)
        for i in mo:
            # details_per_mo = self.work_order_per_mo(i[0])
            # print("the details in the details_per_mo",details_per_mo)
            mo_work_orders = self.env['mrp.workorder'].search(
                [('production_id', '=', i[0]), ('company_id', '=', self.company_id.id)])
            print("the work order is", mo_work_orders)

            if mo_work_orders:
                work_order_names = []
                # work_order_names = ''

                for wo in mo_work_orders:
                    data = {}
                    work_order_names.append(wo.name)
                    # work_order_names+=wo.name+"      "
                    print("manufacturng name", wo.production_id.name)
                    print ("woooo", wo.name)
                    print("work order process id", wo.process_id.name)
                    data.update({
                        'id':i[0],
                        'mo_names':i[1],
                        'label': wo.name,
                        'value': wo.qty_producing,
                        # 'type': wo.qty_produced
                    })
                    data_list.append(data)
                print("the values in the data are:",work_order_names)
                print("the values in the data are:",data_list)

                [graph_title, graph_key] = self._graph_title_and_key()
        return [{'values': data_list, 'title': graph_title, 'key': graph_key}]


    @api.multi
    def work_order_per_mo(self):
        data_list1 = []
        data_list3 = []
        data_list4 = []
        data_list6 = []


        if self.mo_data:
            mo_work_orders = self.env['mrp.workorder'].search(
                [('production_id', '=', self.mo_data.id), ('company_id', '=', self.company_id.id)])
            if mo_work_orders:
                work_order_names = []
                # work_order_names = ''
                for wo in mo_work_orders:
                    data1 = {}
                    data3 = {}
                    data4 = {}
                    data6 = {}
                    work_order_names.append(wo.name)
                    wo_trace = self.env['mrp.workorder.todo.checklist'].search([('work_order_id', '=', wo.id)])
                    print("the data in wo trace",wo_trace)
                    rejected_qty, rework_qty, pending_qty = 0, 0, 0
                    # if wo_trace:
                    for trace in wo_trace:
                        rejected_qty = trace.rejected_qty
                        rework_qty = trace.rework_qty
                        total_done = trace.total
                        pending_qty = trace.pending_qty

                    data1.update({
                        'y': wo.qty_produced,
                        'x': wo.name,
                        'value': wo.qty_produced,
                        # 'key': wo.name,
                        # 'label': wo.name,
                        # 'name':wo.name
                        # 'type': 'Future',
                        # 'color': 'blue',
                        # 'area': True,
                    }

                    )

                    data3.update({
                        'y': rejected_qty,
                        'x': wo.name,
                        'value': rejected_qty,
                    })
                    data4.update({
                        'y': rework_qty,
                        'x': wo.name,
                        'value': rework_qty,
                    })

                    data6.update({
                        'y': pending_qty,
                        'x': wo.name,
                        'value': pending_qty,
                    })
                    data_list1.append(data1)
                    data_list3.append(data3)
                    data_list4.append(data4)
                    data_list6.append(data6)
                    # key = wo.name

                [graph_title, graph_key] = self._graph_title_and_key()
        return [{'values': data_list1, 'key': 'Quantity Produced'},
                {'values': data_list3, 'key': 'Rejected Quantity'}, {'values': data_list4, 'key': 'Rework Quantity'},
                {'values': data_list6, 'key': 'Pending Quantity'}]

    def _graph_title_and_key(self):
        return ['', _('Production Quantity')]


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    _description = 'mrp.workorder'


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def create(self, vals):
        res = super(MrpProduction, self).create(vals)

        print ("resssssss data", res.id)

        self.env['manufacturing.dashboard'].create({
            'mo_data': res.id,
            'company_id': res.company_id.id,
            'color': random.choice([1, 2, 3, 4, 5, 6, 4, 7, 8, 9]),
            'name': res.name
        })
        return res
