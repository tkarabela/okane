from decimal import Decimal
from io import BytesIO
from lxml import etree
from lxml.etree import _Element
from pathlib import Path
from pydantic import BaseModel
from typing import Self
import datetime
import os

from okane.helpers import get_text_or_none, flatten_dict

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore[assignment]


class BankId(BaseModel):
    """
    FinancialInstitutionIdentification per camt.053

    Attributes:
        bic: BIC bank code (SWIFT)
        id: Czech bank code
    """
    bic: str | None = None
    id: str | None = None

    def __str__(self) -> str:
        return self.bic or self.id or ""

    @classmethod
    def from_xml(cls, root: _Element) -> Self | None:
        bic = get_text_or_none(root, "BIC") or get_text_or_none(root, "BICFI")
        id = get_text_or_none(root, "Othr/Id")

        if bic or id:
            return cls(
                bic=bic,
                id=id,
            )
        else:
            return None


class AccountId(BaseModel):
    """
    AccountIdentification4Choice per camt.053

    Attributes:
        iban: IBAN account code
        id: Czech account code
    """
    iban: str | None = None
    id: str | None = None

    def __str__(self) -> str:
        return self.iban or self.id or ""

    @classmethod
    def from_xml(cls, root: _Element) -> Self | None:
        iban = get_text_or_none(root, "IBAN")
        id = get_text_or_none(root, "Othr/Id")

        if iban or id:
            return cls(
                iban=iban,
                id=id,
            )
        else:
            return None


class TransactionRef(BaseModel):
    message_id: str | None = None
    end_to_end_id: str | None = None
    account_servicer_ref: str | None = None
    payment_invocation_id: str | None = None
    instruction_id: str | None = None
    mandate_id: str | None = None
    cheque_number: str | None = None
    clearing_system_ref: str | None = None

    def __str__(self) -> str:
        return ", ".join(f"{k}={v}" for k, v in self.model_dump().items() if v is not None)

    @classmethod
    def from_xml(cls, root: _Element | None) -> Self:
        if root is None:
            return cls()
        else:
            return cls(
                message_id=get_text_or_none(root, "MsgId"),
                account_servicer_ref=get_text_or_none(root, "AcctSvcrRef"),
                payment_invocation_id=get_text_or_none(root, "PmtInfId"),
                instruction_id=get_text_or_none(root, "InstrId"),
                end_to_end_id=get_text_or_none(root, "EndToEndId"),
                mandate_id=get_text_or_none(root, "MndtId"),
                cheque_number=get_text_or_none(root, "ChqNb"),
                clearing_system_ref=get_text_or_none(root, "ClrSysRef"),
            )


class Balance(BaseModel):
    amount: Decimal
    currency: str
    date: datetime.date


class Transaction(BaseModel):
    ref: TransactionRef
    entry_ref: str
    amount: Decimal
    currency: str
    val_date: datetime.date
    remote_info: str | None
    additional_transaction_info: str | None
    related_account_id: AccountId | None
    related_account_bank_id: BankId | None

    @property
    def info(self) -> str:
        remote_info = (self.remote_info or "").strip()
        additional_transaction_info = (self.additional_transaction_info or "").strip()

        if remote_info and additional_transaction_info:
            if remote_info == additional_transaction_info:
                return remote_info
            else:
                return f"{remote_info} / {additional_transaction_info}"
        else:
            return remote_info or additional_transaction_info

    @property
    def related_account(self) -> str | None:
        if self.related_account_id is None and self.related_account_bank_id is None:
            return None
        else:
            return f"{self.related_account_id}/{self.related_account_bank_id}"


class BankToCustomerStatement(BaseModel):
    statement_id: str
    created_time: datetime.datetime
    from_time: datetime.datetime
    to_time: datetime.datetime
    account_id: AccountId
    opening_balance: Balance | None
    closing_balance: Balance | None
    transactions: list[Transaction]

    @classmethod
    def from_file(cls, path: os.PathLike[str] | str) -> "BankToCustomerStatement":
        raw_xml = Path(path).read_bytes()
        raw_xml_no_namespace = raw_xml.replace(b'xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"', b"")
        tree = etree.parse(BytesIO(raw_xml_no_namespace))
        root = tree.getroot()

        from okane.parser import parse_statement
        return parse_statement(root)

    def as_dataframe(self) -> "pd.DataFrame":
        if pd is None:
            raise RuntimeError("pandas is not installed")

        rows = [flatten_dict(tx.model_dump(), prefix="transaction.") for tx in self.transactions]
        df = pd.DataFrame.from_records(rows)
        df["statement.id"] = self.statement_id
        df["statement.account_id"] = str(self.account_id)
        return df
