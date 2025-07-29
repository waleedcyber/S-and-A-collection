from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import Order
from datetime import datetime
from typing import List, Optional
from schemas import OrderOut  # Assuming you created this

router = APIRouter()


# ✅ View orders (all or by status)
@router.get("/orders", response_model=List[OrderOut])
def get_orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.payment_status == status)
    return query.order_by(Order.timestamp.desc()).all()

 # mark as paid order
@router.patch("/orders/{order_id}/mark-paid")
def mark_order_paid(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.payment_status = "paid"
    order.paid_at = datetime.utcnow()
    db.commit()
    return {"message": "Order marked as paid"}


# ✅ View paid orders
@router.get("/paid-orders")
def get_paid_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.payment_status == "paid").order_by(Order.paid_at.desc()).all()
    return orders


# ✅ Mark order as paid using integer ID
@router.put("/orders/by-id/{order_id}/mark-paid")
def mark_order_paid_by_id(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.payment_status = "paid"
    order.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(order)
    return {"message": f"Order {order.id} marked as paid"}


# ✅ Mark order as paid using custom string order_id and ref
@router.post("/orders/by-code/{order_id}/mark-paid")
def mark_order_paid_by_code(order_id: str, reference: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.payment_status = "paid"
    order.payment_reference = reference
    order.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    return {
        "message": "Order marked as paid",
        "order": {
            "order_id": order.order_id,
            "payment_status": order.payment_status,
            "paid_at": order.paid_at.isoformat()
        }
    }


