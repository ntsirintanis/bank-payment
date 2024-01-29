# Copyright - 2024 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""WebHook for Adyen notifications."""
import logging

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment_adyen.controllers.main import AdyenController

_logger = logging.getLogger(__name__)


class AdyenRefundController(AdyenController):
    """Set refund status via webhook"""

    @http.route()
    def adyen_webhook(self):
        res = super().adyen_webhook()
        data = request.dispatcher.jsonrequest
        for notification_item in data["notificationItems"]:
            notification_data = notification_item["NotificationRequestItem"]
            event_code = notification_data["eventCode"]
            if not event_code == "REFUND":
                continue
            success = notification_data["success"] == "true"
            try:
                tx_sudo = (
                    request.env["payment.transaction"]
                    .sudo()
                    ._get_tx_from_notification_data("adyen", notification_data)
                )
            except ValidationError as err:
                if success and res == "[accepted]":
                    provider_reference = notification_data.get("pspReference")
                    source_reference = notification_data.get("originalReference")
                    _logger.warning(
                        "Transaction with reference %s and source %s "
                        "does not exist in odoo, skipping."
                        % (provider_reference, source_reference)
                    )
                    continue
                else:
                    raise err
            if not success:
                tx_sudo.invoice_ids.write(
                    {
                        "refund_status": "failed",
                        "refund_failure_reason": notification_data["reason"],
                    }
                )
            else:
                tx_sudo.invoice_ids.write(
                    {
                        "refund_status": "done",
                        "refund_failure_reason": False,
                    }
                )
        return res
