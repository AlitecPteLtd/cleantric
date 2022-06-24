from odoo import http,tools, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import get_records_pager, CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from werkzeug.exceptions import Forbidden, NotFound

    
class CustomerPortal(CustomerPortal):
    MANDATORY_BILLING_FIELDS = ["name", "mobile", "email", "street", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "street2", "city"]
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

    @http.route(['/appointments/account'], type='http', auth='public', methods=['POST'], website=True)
    def ba_account_details(self, **post):
        """
        The route to create partner / update current partner contact details

        Methods:
         * _check_ba_portal_user_rights
         * _prepare_session_order
         * _check_reservations
         * _contact_details_validate
         * _reservation_details_validate
         * _update_session_contact_details of website.business.appointment

        Returns:
         * if error - page with errors
         * otherwise redirect to the new step

        Extra info:
         * even here we check for reservations expiration for the location reload did not take place
         * we keep vals in both website.order and reservations. The former is required to recover values when
           reservations are cancelled in the process of scheduling
        """
        values = self._check_ba_portal_user_rights()
        session_appointment_id = self._prepare_session_order()
        miss1, miss2, four_step = session_appointment_id._check_reservations(
            session_appointment_id.url_resource_ids, session_appointment_id.url_service_id
        )
        if four_step:
            res = request.redirect("/appointments/4?progress_step=4")
        else:
            error, error_message, contact_values = self._contact_details_validate(session_appointment_id, post)
            values.update(contact_values)
            r_error, r_error_message, reservation_vals = self._reservation_details_validate(request.params)
            values.update(reservation_vals)
            error.update(r_error)
            error_message += r_error_message
            values.update({
                'mobile': session_appointment_id.partner_id.mobile or False,
                'street': session_appointment_id.partner_id.street or '',
                'street2': session_appointment_id.partner_id.street2 or '',
                'city': session_appointment_id.partner_id.city or '',
                'country_id': session_appointment_id.partner_id.country_id and session_appointment_id.partner_id.country_id.id or '',
                'state_id': session_appointment_id.partner_id.state_id and session_appointment_id.partner_id.state_id.id or '',
                'zipcode': session_appointment_id.partner_id.zip or ''
            })
            if error:
                error_vals = {}
                for key, val in error.items():
                    if key in ["agree_terms", "email", "phone", "mobile"]:
                        # to save them and show after reload, but not write. Not all fields, since binary are not safe eval
                        error_vals.update({key: values.get(key)})
                    if values.get(key):
                        # we do not write fields with errors
                        del values[key]
                values.update({
                    "error": error,
                    "error_message": error_message,
                    "error_vals": error_vals,
                })

                session_appointment_id._update_session_contact_details(values, False)
                res = request.redirect("/appointments/5?progress_step=5")
            else:
                values.update({
                    "error": False,
                    "error_message": False,
                    "error_vals": False,
                    "website_id": request.website.id,
                })
                session_appointment_id._update_session_contact_details(values, True)
                res = request.redirect("/appointments/6?progress_step=6")
        return res
    
    def _contact_details_validate(self, session_appointment_id, data):
        """
        The method to check contact details values

        Args:
         * session_appointment_id - website.business.order
         * data - dict of values

        Methods:
         * _return_website_ba_contact_fields of website
         * _check_existing_duplicates

        Returns:
         * dict if field names with errors
         * list of error
         * business.appointment.core values
        """
        error = dict()
        error_message = []
        all_fields, mandatory_fields = request.website._return_website_ba_contact_fields()
        mandatory_fields+=["mobile","street","street2","zipcode","country_id"]
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))
        if data.get("phone"):
            try:
                raise_error = "phone" in mandatory_fields
                res = session_appointment_id._format_phone_number(data.get("phone"), raise_error)
                data["phone"] = res
            except Exception as e:
                error["phone"] = 'error'
                error_message.append(_('Invalid Phone! {}'.format(e)))
        if data.get("mobile"):
            try:
                raise_error = "mobile" in mandatory_fields
                res = session_appointment_id._format_phone_number(data.get("mobile"), raise_error)
                data["mobile"] = res
            except Exception as e:
                error["mobile"] = 'error'
                error_message.append(_('Invalid Mobile! {}'.format(e)))
        existing_partner = session_appointment_id._check_existing_duplicates(
            data.get('email'), data.get("mobile"), data.get("phone"), session_appointment_id.partner_id,
        )
        if existing_partner:
            error["email"] = 'error'
            error["mobile"] = 'error'
            error["phone"] = 'error'
            error_message.append(_(
                'Sorry, but the user with the same email, phone, or mobile already exists! Please change or log in!'
            ))
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))
        values = {key: data[key] for key in all_fields if key in data}
        return error, error_message, values

    def _step5_prepare_values(self, session_appointment_id, durl="", **kw):

        res = super(CustomerPortal, self)._step5_prepare_values(session_appointment_id=session_appointment_id,durl=durl,**kw)
        res.update({
            'mobile': session_appointment_id.partner_id.mobile or '',
            'street': session_appointment_id.partner_id.street or '',
            'street2': session_appointment_id.partner_id.street2 or '',
            'city': session_appointment_id.partner_id.city or '',
            'country_id': session_appointment_id.partner_id.country_id and session_appointment_id.partner_id.country_id.id or '',
            'state_id': session_appointment_id.partner_id.state_id and session_appointment_id.partner_id.state_id.id or '',
            'zipcode': session_appointment_id.partner_id.zip or ''
        })
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

    def _get_mandatory_fields_billing(self, country_id=False):
        res = super(WebsiteSale, self)._get_mandatory_fields_billing(country_id=country_id)
        res.remove('city')
        if country_id:
            country = request.env['res.country'].browse(country_id)
            if country.state_required:
                res.remove('state_id')
            if country.zip_required:
                res.remove('zip')
        return res

    def _get_mandatory_fields_shipping(self, country_id=False):
        res = super(WebsiteSale, self)._get_mandatory_fields_shipping(country_id=country_id)
        res.remove('city')
        if country_id:
            country = request.env['res.country'].browse(country_id)
            if country.state_required:
                res.remove('state_id')
            if country.zip_required:
                res.remove('zip')
        return res

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ('edit', 'billing')
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
                    if order.partner_id.commercial_partner_id.id == partner_id:
                        mode = ('new', 'shipping')
                        partner_id = -1
                    elif partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else: # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.with_context(not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                            (not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(kw.get('callback') or '/shop/confirm_order')

        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'error': errors,
            'callback': kw.get('callback'),
            'only_services': order and order.only_services
        }
        if not kw.get('partner_id') != -1:
            partner = request.env['res.partner'].sudo().browse(int(kw.get('partner_id')))
            render_values.update({
                'mobile': partner.mobile or '',
                'street': partner.street or '',
                'street2': partner.street2 or '',
                'city': partner.city or '',
                'country_id': partner.country_id and partner.country_id.id or '',
                'state_id': partner.state_id and partner.state_id.id or '',
                'zipcode': partner.zip or ''
            })
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("website_sale.address", render_values)


class WebsiteForm(http.Controller):

    @http.route('/contactus', type="http", auth="public", website="True")
    def contact_us_data_form(self, **kwargs):
        """
           this method use contact us view display"""
        return request.render('cleantric_operation.contact_us_form_data_new')



