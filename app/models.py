from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class InvoiceStatus(str, Enum):
    """Statuses accepted by the invoice API."""

    PAID = "Paid"
    UNPAID = "Unpaid"
    OVERDUE = "Overdue"
    DRAFT = "Draft"
    PENDING = "Pending"


class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(
        index=True,
        min_length=1,
        description="Client's display name.",
        examples=["Ada Lovelace"],
    )
    email: str = Field(
        description="Client's contact email address.",
        examples=["ada@example.com"],
    )
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = Field(default="Nigeria")
    status: str = Field(default="Active")  # Active, Inactive
    owner_email: str = Field(default="default@sapi.com", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_number: str = Field(
        unique=True,
        index=True,
        min_length=1,
        description="Unique invoice identifier; cannot be empty.",
        examples=["SAPI-INV-0001"],
    )
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client_name: str = Field(
        description="Name of the client receiving this invoice.",
        examples=["Ada Lovelace"],
    )
    client_email: Optional[str] = None
    service_summary: Optional[str] = Field(default="Design Services")  # Subtitle shown under Client Name in tables
    issue_date: str = Field(default="10 May 2026")
    due_date: Optional[str] = Field(default="24 May 2026")
    amount: float = Field(
        gt=0,
        description="Invoice total. Must be greater than zero.",
        examples=[50000.0],
    )
    currency: str = Field(default="NGN")
    status: str = Field(
        default=InvoiceStatus.UNPAID.value,
        description="One of the supported invoice statuses.",
        json_schema_extra={
            "enum": [status.value for status in InvoiceStatus],
        },
        examples=[InvoiceStatus.UNPAID.value],
    )
    line_items_json: str = Field(default="[]")  # JSON string storing [{description, subtitle, qty, rate, amount}]
    notes: Optional[str] = None
    stellar_memo: Optional[str] = None  # e.g. SAPI-INV-0031
    stellar_tx_hash: Optional[str] = None  # Stores on-chain TX hash when paid via Stellar
    owner_email: str = Field(default="default@sapi.com", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """Reject statuses outside the public invoice status vocabulary."""
        try:
            return InvoiceStatus(value).value
        except ValueError as exc:
            allowed = ", ".join(status.value for status in InvoiceStatus)
            raise ValueError(f"Status must be one of: {allowed}") from exc
