from odoo import http,tools, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import get_records_pager, CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale

    
class CustomerPortal(CustomerPortal):
    MANDATORY_BILLING_FIELDS = ["name", "email"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "mobile", "street", "street2", "city", "country_id"]

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


class WebsiteSale(WebsiteSale):
    """
            this controller inherit shop page and the user not login then force fully
             redirect login page.
    """
    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=WebsiteSale.sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):

        if not request.session.uid:
            return request.redirect("/web/login?redirect=/shop")
        res = super(WebsiteSale, self).shop(page=page, category=category, search=search,min_price=min_price, max_price=max_price, ppg=ppg, **post)
        return res


class WebsiteForm(http.Controller):

    @http.route('/contactus', type="http", auth="public", website="True")
    def contact_us_data_form(self, **kwargs):
        """
           this method use contact us view display"""
        return request.render('cleantric_operation.contact_us_form_data_new')



