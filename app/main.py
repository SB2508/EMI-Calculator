from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import models
from app.database import engine, get_db
from app.emi_logic import build_amortization_schedule, calculate_totals
from app.schemas import (
    AmortizationResponse,
    EMIRequest,
    EMIResponse,
    HistoryItem,
    PrepaymentRequest,
    PrepaymentResponse,
)

# Creates tables on startup if they don't exist yet
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EMI Loan Calculator API",
    description="Calculates EMI, amortization schedules, and prepayment impact for loans.",
    version="1.0.0",
)

# Allow the frontend (hosted anywhere) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/calculate/emi", response_model=EMIResponse)
def calculate_emi_endpoint(payload: EMIRequest, db: Session = Depends(get_db)):
    emi, total_payment, total_interest = calculate_totals(
        payload.principal, payload.annual_rate, payload.tenure_months
    )

    # Log every calculation — this is your "real usage" evidence
    record = models.Calculation(
        principal=payload.principal,
        annual_rate=payload.annual_rate,
        tenure_months=payload.tenure_months,
        emi=emi,
        total_interest=total_interest,
    )
    db.add(record)
    db.commit()

    return EMIResponse(
        emi=emi, total_payment=total_payment, total_interest=total_interest
    )


@app.post("/calculate/amortization", response_model=AmortizationResponse)
def amortization_endpoint(payload: EMIRequest):
    emi, total_payment, total_interest = calculate_totals(
        payload.principal, payload.annual_rate, payload.tenure_months
    )
    schedule = build_amortization_schedule(
        payload.principal, payload.annual_rate, payload.tenure_months
    )
    return AmortizationResponse(
        emi=emi,
        total_payment=total_payment,
        total_interest=total_interest,
        schedule=schedule,
    )


@app.post("/calculate/prepayment", response_model=PrepaymentResponse)
def prepayment_endpoint(payload: PrepaymentRequest):
    # Original schedule (no prepayment)
    original_schedule = build_amortization_schedule(
        payload.principal, payload.annual_rate, payload.tenure_months
    )
    original_total_interest = round(
        sum(row.interest_component for row in original_schedule), 2
    )

    # Schedule with prepayment applied
    new_schedule = build_amortization_schedule(
        payload.principal,
        payload.annual_rate,
        payload.tenure_months,
        prepayment_amount=payload.prepayment_amount,
        prepayment_month=payload.prepayment_month,
    )
    new_total_interest = round(sum(row.interest_component for row in new_schedule), 2)

    return PrepaymentResponse(
        original_tenure_months=len(original_schedule),
        new_tenure_months=len(new_schedule),
        original_total_interest=original_total_interest,
        new_total_interest=new_total_interest,
        interest_saved=round(original_total_interest - new_total_interest, 2),
        schedule=new_schedule,
    )


@app.get("/history", response_model=list[HistoryItem])
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    records = (
        db.query(models.Calculation)
        .order_by(models.Calculation.id.desc())
        .limit(limit)
        .all()
    )
    return records


# Serves the simple frontend at /static/index.html
app.mount("/static", StaticFiles(directory="app/static"), name="static")
