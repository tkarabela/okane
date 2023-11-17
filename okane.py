#!/usr/bin/env python3

# Copyright (c) 2023 Tomas Karabela
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Okane
=====

Python parser for bank statements in camt.053 XML format, in dialect
used by the Czech Banking Association (ČBA).

"""

import argparse
import sys
from typing import Optional, Any
from lxml import etree
from lxml.etree import _Element
from io import BytesIO, StringIO
from pydantic import BaseModel
from enum import Enum
import datetime
from decimal import Decimal
import warnings
try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore[assignment]


__version__ = "0.1.0"


def get_text_or_none(e: _Element | None, path: str | None = None, strip: bool = True) -> str | None:
    if e is None:
        return None
    else:
        if path is not None:
            e = e.find(path)

        if e is None:
            return None
        else:
            text = e.text
            if strip and text is not None:
                text = text.strip()
            return text


def get_text(e: _Element | None, path: str | None = None, strip: bool = True) -> str:
    text = get_text_or_none(e, path, strip)
    if text is None:
        raise ValueError("Missing mandatory element")
    return text


def get_element(root: _Element, path: str) -> _Element:
    e = root.find(path)
    if e is None:
        raise ValueError(f"Missing mandatory element ({path})")
    return e


def get_attribute(e: _Element, attr: str) -> str:
    value = e.attrib[attr]
    return str(value)


class CreditOrDebit(str, Enum):
    """CreditDebitCode per camt.053"""
    CRDT = "CRDT"
    DBIT = "DBIT"


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
    def from_xml(cls, root: _Element) -> Optional["BankId"]:
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
    def from_xml(cls, root: _Element) -> Optional["AccountId"]:
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
    def from_xml(cls, root: _Element | None) -> "TransactionRef":
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
    def from_file(cls, path: str) -> "BankToCustomerStatement":
        with open(path, "rb") as fp:
            raw_xml = fp.read()

        raw_xml_no_namespace = raw_xml.replace(b'xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"', b"")
        tree = etree.parse(BytesIO(raw_xml_no_namespace))
        root = tree.getroot()

        return parse_statement(root)

    def as_dataframe(self) -> "pd.DataFrame":
        if pd is None:
            raise RuntimeError("pandas is not installed")

        rows = [flatten_dict(tx.model_dump(), prefix="transaction.") for tx in self.transactions]
        df = pd.DataFrame.from_records(rows)
        df["statement.id"] = self.statement_id
        df["statement.account_id"] = str(self.account_id)
        return df


def parse_statement(root: _Element) -> BankToCustomerStatement:
    stmt = get_element(root, "BkToCstmrStmt/Stmt")
    statement_id = get_text(stmt.find("Id"))
    created_time = datetime.datetime.fromisoformat(get_text(stmt, "CreDtTm"))
    from_time = datetime.datetime.fromisoformat(get_text(stmt, "FrToDt/FrDtTm"))
    to_time = datetime.datetime.fromisoformat(get_text(stmt, "FrToDt/ToDtTm"))
    account_id = AccountId.from_xml(get_element(stmt, "Acct/Id"))
    opening_balance = None
    closing_balance = None

    if account_id is None:
        raise ValueError("Missing AccountID elements")

    for bal in stmt.findall("Bal"):
        bal_date = parse_date_isoformat(get_text(bal, "Dt/Dt"))
        amt = get_element(bal, "Amt")
        bal_currency = get_attribute(amt, "Ccy")
        amount = Decimal(get_text(amt))
        tmp = CreditOrDebit(get_text(bal, "CdtDbtInd"))
        if tmp == CreditOrDebit.DBIT:
            amount *= -1
        tmp2 = get_text(bal, "Tp/CdOrPrtry/Cd")

        balance = Balance(
            amount=amount,
            currency=bal_currency,
            date=bal_date
        )

        if tmp2 == "PRCD":
            opening_balance = balance
        elif tmp2 == "CLBD":
            closing_balance = balance

    transactions = parse_transactions(stmt)

    return BankToCustomerStatement(
        statement_id=statement_id,
        created_time=created_time,
        from_time=from_time,
        to_time=to_time,
        account_id=account_id,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        transactions=transactions
    )


def parse_transactions(stmt: _Element) -> list[Transaction]:
    return [parse_transaction(ntry) for ntry in stmt.findall("Ntry")]


def parse_transaction(ntry: _Element) -> Transaction:
    entry_ref = get_text(ntry, "NtryRef")
    ref = TransactionRef.from_xml(ntry.find("NtryDtls/TxDtls/Refs"))

    amt = get_element(ntry, "Amt")
    currency = get_attribute(amt, "Ccy")
    amount = Decimal(get_text(amt))
    tmp = CreditOrDebit(get_text(ntry, "CdtDbtInd"))
    if tmp == CreditOrDebit.DBIT:
        amount *= -1

    val_date = parse_date_isoformat(get_text(ntry, "ValDt/Dt"))

    remote_info = get_text_or_none(ntry, "NtryDtls/TxDtls/RmtInf/Ustrd")
    additional_transaction_info = get_text_or_none(ntry, "NtryDtls/TxDtls/AddtlTxInf")

    if (dbtr_acct_id := ntry.find("NtryDtls/TxDtls/RltdPties/DbtrAcct/Id")) is not None:
        related_account_id = AccountId.from_xml(dbtr_acct_id)
    elif (cdtr_acct_id := ntry.find("NtryDtls/TxDtls/RltdPties/CdtrAcct/Id")) is not None:
        related_account_id = AccountId.from_xml(cdtr_acct_id)
    else:
        related_account_id = None

    if (dbtr_agt_id := ntry.find("NtryDtls/TxDtls/RltdAgts/DbtrAgt/FinInstnId")) is not None:
        related_account_bank_id = BankId.from_xml(dbtr_agt_id)
    elif (cdtr_agt_id := ntry.find("NtryDtls/TxDtls/RltdAgts/CdtrAgt/FinInstnId")) is not None:
        related_account_bank_id = BankId.from_xml(cdtr_agt_id)
    else:
        related_account_bank_id = None

    return Transaction(
        entry_ref=entry_ref,
        ref=ref,
        amount=amount,
        currency=currency,
        val_date=val_date,
        remote_info=remote_info,
        additional_transaction_info=additional_transaction_info,
        related_account_id=related_account_id,
        related_account_bank_id=related_account_bank_id,
    )


def parse_date_isoformat(s: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        warnings.warn(f"Invalid isoformat string: {s!r}", RuntimeWarning)
        return datetime.date.fromisoformat(s[:10])


def flatten_dict(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    output = {}
    for k, v in d.items():
        if isinstance(v, dict):
            output.update(flatten_dict(v, prefix=f"{prefix}{k}."))
        else:
            output[f"{prefix}{k}"] = v
    return output


class OutputFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_files", nargs="+", metavar="statement.xml",
                        help="path to input camt.053 XML file(s)")
    parser.add_argument("--version", "-V", action="version", version=__version__)
    parser.add_argument("--output", "-o", metavar="FILE", default="-", help="path to output file "
                        "(default: write to stdout)")
    parser.add_argument("--format", "-f", choices=[fmt.value for fmt in OutputFormat],
                        type=OutputFormat, default=OutputFormat.JSON, help="set output format (default: json)")
    parser.add_argument("--no-indent", action="store_true", help="do not indent JSON output files")

    args = parser.parse_args(argv)
    input_files = args.input_files
    output_path = args.output
    output_format = args.format
    no_indent = args.no_indent

    statements = [BankToCustomerStatement.from_file(path) for path in input_files]

    output_bytes = b""

    match output_format:
        case OutputFormat.JSON:
            for statement in statements:
                output_bytes += statement.model_dump_json(indent=None if no_indent else 4).encode("utf-8")
                output_bytes += b"\n"
        case OutputFormat.CSV:
            dfs = []
            for statement in statements:
                df = statement.as_dataframe()
                dfs.append(df)
            assert pd is not None
            all_df = pd.concat(dfs)
            buf = StringIO()
            all_df.to_csv(buf, index=False)
            output_bytes = buf.getvalue().encode("utf-8")
        case OutputFormat.XLSX:
            dfs = []
            for statement in statements:
                df = statement.as_dataframe()
                dfs.append(df)
            assert pd is not None
            all_df = pd.concat(dfs)
            buf_bin = BytesIO()
            all_df.to_excel(buf_bin, index=False)
            output_bytes = buf_bin.getvalue()
        case _:
            raise NotImplementedError(f"Unsupported output format {output_format}")

    if output_path == "-":
        sys.stdout.buffer.write(output_bytes)
    else:
        with open(output_path, "wb") as fp:
            fp.write(output_bytes)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
