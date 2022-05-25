from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import get_records_pager, CustomerPortal

    
class CustomerPortal(CustomerPortal):
    """
        this controller inherit appointment page and the user not login then force fully
         redirect login page.
    """
    @http.route(['/appointments', '/appointments/page/<int:page>',
                 '/appointments/<int:active_step>',
                 '/appointments/<int:active_step>/page/<int:page>',
                 ], type='http', auth="public", website=True)
    def ba_super_controller(self, active_step=None, url_ba_type_id=None, url_resource_ids=None, url_service_id=None,
                            progress_step=None, confirmation_code=None, page=1, sortby=None, filterby=None, search=None,
                            search_in='name', **kw):

        if not request.session.uid:
            return request.redirect("/web/login?redirect=/appointments")
        res = super(CustomerPortal, self).ba_super_controller(active_step=active_step, url_ba_type_id=url_ba_type_id, url_resource_ids=url_resource_ids, url_service_id=url_service_id,
                            progress_step=progress_step, confirmation_code=confirmation_code, page=page, sortby=sortby, filterby=filterby, search=search,
                            search_in=search_in, **kw)
        return res








