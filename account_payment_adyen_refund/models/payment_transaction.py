# Copyright - 2024 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Support Adyen Refund."""
from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _create_refund_transaction(self, amount_to_refund=None, **custom_create_values):
        """Do not create a second transaction when sending to adyen"""
        if self.provider_code != "adyen":
            return super()._create_refund_transaction(
                amount_to_refund=amount_to_refund, **custom_create_values
            )
        return self
