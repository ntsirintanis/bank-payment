# Copyright - 2024 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Support Adyen Refund."""
from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res["adyen_refund"] = {
            "mode": "multi",
            "domain": [("type", "=", "bank")],
        }
        return res
