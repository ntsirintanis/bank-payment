# Copyright - 2024 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Support Adyen Refund."""
from odoo import _, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    """Support Adyen Refund."""

    _inherit = "account.payment"

    def _check_adyen_refund_request(self):
        """validate payment for Adyen refund and send it."""
        self.ensure_one()
        invoice = self.reconciled_invoice_ids
        # Refunds via Adyen work only for single invoices.
        if len(invoice) != 1:
            raise UserError(
                _("You can only refund a single invoice per payment through Adyen")
            )
        # Check validity of invoices for adyen refund.
        if invoice.refund_status != "none":
            raise UserError(_("Invoice %s already submitted for refund") % invoice.name)
        if invoice.move_type != "out_refund":
            raise UserError(_("Invoice %s is not a customer refund") % invoice.name)
        if not invoice.transaction_id:
            raise UserError(_("PsP number not filled in invoice %s") % invoice.name)
        if not invoice.invoice_origin:
            raise UserError(_("Invoice origin not filled in invoice %s") % invoice.name)

    def _send_adyen_refund_request(self):
        """Actually request refund from Adyen."""
        self.ensure_one()
        transaction_model = self.env["payment.transaction"]
        invoice = self.reconciled_invoice_ids
        reference = self._compute_reference(invoice.invoice_origin)
        values = {
            "reference": reference,
            "amount": float(self.amount),
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "payment_id": self.id,
            "provider_id": self.env.ref("payment.payment_provider_adyen").id,
            "invoice_ids": [(4, invoice.id)],
        }
        refund_tx = transaction_model.create(values)
        self.write({"payment_transaction_id": refund_tx.id})
        invoice.write({"refund_status": "send"})
        self.env.cr.commit()
        refund_tx._send_refund_request()
        invoice.refund_status = "submitted"

    def _compute_reference(self, reference):
        """Adjust reference to avoid uniqueness constraint"""
        existing_count = self.env["payment.transaction"].search_count(
            [("reference", "=like", reference + "%")]
        )
        if not existing_count:
            return reference
        return reference + "-" + str(existing_count)
