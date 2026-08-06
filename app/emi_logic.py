"""
Core EMI calculation logic.

Formula:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

Where:
    P = principal loan amount
    r = monthly interest rate (annual_rate / 12 / 100)
    n = tenure in months
"""

from typing import List, Optional
from app.schemas import AmortizationRow


def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Return the fixed monthly EMI amount."""
    if annual_rate == 0:
        return round(principal / tenure_months, 2)

    r = annual_rate / 12 / 100
    factor = (1 + r) ** tenure_months
    emi = principal * r * factor / (factor - 1)
    return round(emi, 2)


def calculate_totals(principal: float, annual_rate: float, tenure_months: int):
    """Return (emi, total_payment, total_interest)."""
    emi = calculate_emi(principal, annual_rate, tenure_months)
    total_payment = round(emi * tenure_months, 2)
    total_interest = round(total_payment - principal, 2)
    return emi, total_payment, total_interest


def build_amortization_schedule(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    prepayment_amount: Optional[float] = None,
    prepayment_month: Optional[int] = None,
) -> List[AmortizationRow]:
    """
    Build a month-by-month schedule.
    If prepayment_amount and prepayment_month are given, the lump sum is
    deducted from the outstanding balance at that month, shortening the loan.
    """
    r = annual_rate / 12 / 100
    emi = calculate_emi(principal, annual_rate, tenure_months)

    schedule = []
    balance = principal
    month = 1
    # A payment this small or smaller just closes out rounding drift —
    # fold it into the previous installment instead of adding a stray row.
    CLOSEOUT_THRESHOLD = 1.0

    while balance > 0 and month <= tenure_months * 2:  # safety cap
        interest_component = round(balance * r, 2)
        principal_component = round(emi - interest_component, 2)

        # Final installment (natural or after prepayment shortens the loan):
        # pay off exactly what's left instead of the fixed EMI amount.
        is_last_scheduled_month = month >= tenure_months
        remaining_after_normal_payment = round(balance - principal_component, 2)

        if principal_component >= balance or (
            is_last_scheduled_month and remaining_after_normal_payment <= CLOSEOUT_THRESHOLD
        ):
            principal_component = round(balance, 2)
            emi_this_month = round(principal_component + interest_component, 2)
            balance = 0.0
        else:
            emi_this_month = emi
            balance = remaining_after_normal_payment

        # Apply prepayment if this is the target month
        if prepayment_amount and prepayment_month and month == prepayment_month:
            balance = round(max(balance - prepayment_amount, 0), 2)
            if balance <= CLOSEOUT_THRESHOLD:
                balance = 0.0

        schedule.append(
            AmortizationRow(
                month=month,
                emi=emi_this_month,
                principal_component=principal_component,
                interest_component=interest_component,
                balance=balance,
            )
        )

        if balance <= 0:
            break
        month += 1

    return schedule
