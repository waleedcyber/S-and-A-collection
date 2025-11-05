from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from db import get_db
from models import Order
from utils.paystack import verify_paystack_transaction_sync
from datetime import datetime
import hmac
import hashlib
import os
import json

router = APIRouter()


@router.post("/payments/verify")
def verify_payment(reference: str, order_id: str, db: Session = Depends(get_db)):
    """Verify a payment using Paystack and mark the order as paid.

    This endpoint should be called by the frontend after the Paystack callback
    to perform server-side verification using the secret key.
    """
    # Verify using Paystack API (sync wrapper)
    data = verify_paystack_transaction_sync(reference)

    # Basic checks
    if data.get("status") != "success":
        raise HTTPException(status_code=400, detail="Payment not successful")

    # Find order by order_id (custom string order_id)
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Idempotency: if already paid, return success
    if order.payment_status == "paid":
        return {"message": "Order already marked as paid"}

    # Optionally verify amount matches
    paystack_amount = data.get("amount")  # in kobo
    try:
        paystack_amount_n = float(paystack_amount) / 100.0
    except Exception:
        paystack_amount_n = None

    if paystack_amount_n is not None and abs(paystack_amount_n - float(order.total)) > 0.01:
        # Amount mismatch — log or raise
        raise HTTPException(status_code=400, detail="Payment amount does not match order total")

    # Update order
    order.payment_status = "paid"
    order.payment_reference = reference
    order.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(order)

    return {"message": "Payment verified and order marked as paid", "order_id": order.order_id}


@router.post("/payments/webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack webhooks.

    Paystack sends POST requests to this endpoint for events such as charge.success.
    We verify the signature using the secret key and update the order accordingly.
    """
    # Read raw body for signature verification
    body = await request.body()
    signature = request.headers.get("x-paystack-signature") or request.headers.get("paystack-signature")

    secret = os.getenv("PAYSTACK_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=500, detail="Paystack secret not configured")

    computed = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(computed, signature or ""):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = json.loads(body.decode("utf-8"))
    event = payload.get("event")
    data = payload.get("data", {})

    # Handle charge.success
    if event == "charge.success":
        reference = data.get("reference")
        # optional: extract metadata/order id if you passed it
        order_code = data.get("metadata", {}).get("order_id") or data.get("reference")

        order = db.query(Order).filter(Order.order_id == order_code).first()
        if order and order.payment_status != "paid":
            order.payment_status = "paid"
            order.payment_reference = reference
            order.paid_at = datetime.utcnow()
            db.commit()

    # Always return 200 to acknowledge
    return {"status": "ok"}
