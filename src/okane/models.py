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
    import polars as pl
except ImportError:
    pl = None  # type: ignore[assignment]


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

    def get_transaction_dataframe(self) -> "pl.DataFrame":
        """
        Return dataframe with transactions

        Refer to fields in `okane.models.Transaction` for meaning of the columns.
        """
        if pl is None:
            raise RuntimeError("polars is not installed")

        rows = [flatten_dict(tx.model_dump()) for tx in self.transactions]
        schema = {
            "ref.message_id": pl.String,
            "ref.end_to_end_id": pl.String,
            "ref.account_servicer_ref": pl.String,
            "ref.payment_invocation_id": pl.String,
            "ref.instruction_id": pl.String,
            "ref.mandate_id": pl.String,
            "ref.cheque_number": pl.String,
            "ref.clearing_system_ref": pl.String,
            "entry_ref": pl.String,
            "amount": pl.Decimal(scale=2),
            "currency": pl.String,
            "val_date": pl.Date,
            "remote_info": pl.String,
            "additional_transaction_info": pl.String,
            "related_account_id.iban": pl.String,
            "related_account_id.id": pl.String,
            "related_account_bank_id.bic": pl.String,
            "related_account_bank_id.id": pl.String,
        }

        return pl.DataFrame(rows, schema=schema)  # type: ignore[arg-type]

    def get_balance_dataframe(self) -> "pl.DataFrame":
        """
        Return dataframe with daily balance (balance at the end of each day)

        The resulting dataframe has columns "val_date" and "amount".
        """
        if pl is None:
            raise RuntimeError("polars is not installed")

        opening_balance = self.opening_balance
        if opening_balance is None:
            raise ValueError("Cannot evaluate balance when opening_balance is not given")

        tx_df = self.get_transaction_dataframe()
        tx_currencies = tx_df.select(
            pl.col("currency").unique()
        )
        match tx_currencies.height:
            case 0:
                pass  # no currency conflict, we have no transactions at all
            case 1:
                if tx_currencies.item() != opening_balance.currency:
                    raise ValueError("Statement has only transactions in currency that does not match account currency")
            case _:
                raise ValueError("Statement has transaction in multiple currencies")

        balance_df = (
            tx_df
            .select("val_date", "amount")
            .sort("val_date")
            .group_by("val_date")
            .sum()
            .with_columns(pl.col("amount").cum_sum() + opening_balance.amount)
        )
        date_df = pl.DataFrame({
            "val_date": pl.date_range(
                start=self.from_time.date(),
                end=self.to_time.date(),
                interval="1d",
                eager=True,
            )
        })

        return (
            date_df
            .join(balance_df, on="val_date", how="left")
            .with_columns(
                pl.when(pl.col("amount").is_not_null().cum_sum() == 0)
                .then(opening_balance.amount)
                .otherwise(pl.col("amount").forward_fill())
                .alias("amount")
            )
        )
