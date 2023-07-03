# Copyright - 2023 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Support Adyen Refund."""
from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.payment_adyen_paybylink.const import API_ENDPOINT_VERSIONS

API_ENDPOINT_VERSIONS.update({"/payments/{}/refunds": 68})


class PaymentTransaction(models.Model):
    """Support Adyen Refund."""

    _inherit = "payment.transaction"

    def _adyen_send_refund(self):
        """Send refund to Adyen."""
        self.ensure_one()
        acquirer = self.acquirer_id
        refund_invoice = self.invoice_ids[0]
        payment_amount = acquirer._adyen_convert_amount(self.amount, self.currency_id)
        data = {
            "merchantAccount": acquirer.adyen_merchant_account,
            "amount": {"value": payment_amount, "currency": self.currency_id.name},
            "reference": refund_invoice.invoice_origin,
        }
        response = acquirer._adyen_make_request(
            url_field_name="adyen_checkout_api_url",
            endpoint="/payments/{}/refunds",
            endpoint_param=refund_invoice.transaction_id,
            payload=data,
            method="POST",
        )
        if response.get("status") != "received":
            raise UserError(
                _("Adyen rejected refund with status %s") % response.get("status")
            )
        psp_reference = response.get("pspReference")
        self.write({"acquirer_reference": psp_reference})
        self._adyen_form_validate(response)
