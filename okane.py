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
from lxml import etree
from lxml.etree import _Element
from io import BytesIO
from pydantic import BaseModel
from enum import Enum
import datetime
from decimal import Decimal
import warnings


__version__ = "0.1.0"


class CreditOrDebit(str, Enum):
    CRDT = "CRDT"
    DBIT = "DBIT"


class Balance(BaseModel):
    amount: Decimal
    currency: str
    date: datetime.date


class Transaction(BaseModel):
    ref: str
    amount: Decimal
    currency: str
    val_date: datetime.date
    remote_info: str | None
    additional_transaction_info: str | None
    related_account: str | None
    related_account_bank: str | None

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


class BankToCustomerStatement(BaseModel):
    statement_id: str
    created_time: datetime.datetime
    from_time: datetime.datetime
    to_time: datetime.datetime
    account_iban: str
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


def parse_statement(root: _Element) -> BankToCustomerStatement:
    stmt = root.find("BkToCstmrStmt/Stmt")
    statement_id = stmt.find("Id").text
    created_time = datetime.datetime.fromisoformat(stmt.find("CreDtTm").text)
    from_time = datetime.datetime.fromisoformat(stmt.find("FrToDt/FrDtTm").text)
    to_time = datetime.datetime.fromisoformat(stmt.find("FrToDt/ToDtTm").text)
    account_iban = stmt.find("Acct/Id/IBAN").text
    opening_balance = None
    closing_balance = None

    for bal in stmt.findall("Bal"):
        bal_date = parse_date_isoformat(bal.find("Dt/Dt").text)
        amt = bal.find("Amt")
        bal_currency = amt.attrib["Ccy"]
        amount = Decimal(amt.text)
        tmp = CreditOrDebit(bal.find("CdtDbtInd").text)
        if tmp == CreditOrDebit.DBIT:
            amount *= -1
        tmp = bal.find("Tp/CdOrPrtry/Cd").text

        balance = Balance(
            amount=amount,
            currency=bal_currency,
            date=bal_date
        )

        if tmp == "PRCD":
            opening_balance = balance
        elif tmp == "CLBD":
            closing_balance = balance

    transactions = parse_transactions(stmt)

    return BankToCustomerStatement(
        statement_id=statement_id,
        created_time=created_time,
        from_time=from_time,
        to_time=to_time,
        account_iban=account_iban,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        transactions=transactions
    )


def parse_transactions(stmt: _Element) -> list[Transaction]:
    return [parse_transaction(ntry) for ntry in stmt.findall("Ntry")]


def parse_transaction(ntry: _Element) -> Transaction:
    ref = ntry.find("NtryRef").text

    amt = ntry.find("Amt")
    currency = amt.attrib["Ccy"]
    amount = Decimal(amt.text)
    tmp = CreditOrDebit(ntry.find("CdtDbtInd").text)
    if tmp == CreditOrDebit.DBIT:
        amount *= -1

    val_date = parse_date_isoformat(ntry.find("ValDt/Dt").text)

    if (rmt_inf_ustrd := ntry.find("NtryDtls/TxDtls/RmtInf/Ustrd")) is not None:
        remote_info = rmt_inf_ustrd.text
    else:
        remote_info = None

    if (addtnl_tx_inf := ntry.find("NtryDtls/TxDtls/AddtlTxInf")) is not None:
        additional_transaction_info = addtnl_tx_inf.text
    else:
        additional_transaction_info = None

    if (elem := ntry.find("NtryDtls/TxDtls/RltdPties/DbtrAcct/Id/Othr/Id")) is not None:
        related_account = elem.text
    elif (elem := ntry.find("NtryDtls/TxDtls/RltdPties/CdtrAcct/Id/Othr/Id")) is not None:
        related_account = elem.text
    else:
        related_account = None

    if (elem := ntry.find("NtryDtls/TxDtls/RltdAgts/DbtrAgt/FinInstnId/Othr/Id")) is not None:
        related_account_bank = elem.text
    elif (elem := ntry.find("NtryDtls/TxDtls/RltdAgts/CdtrAgt/FinInstnId/Othr/Id")) is not None:
        related_account_bank = elem.text
    else:
        related_account_bank = None

    return Transaction(
        ref=ref,
        amount=amount,
        currency=currency,
        val_date=val_date,
        remote_info=remote_info,
        additional_transaction_info=additional_transaction_info,
        related_account=related_account,
        related_account_bank=related_account_bank,
    )


def parse_date_isoformat(s: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        warnings.warn(f"Invalid isoformat string: {s!r}", RuntimeWarning)
        return datetime.date.fromisoformat(s[:10])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", metavar="statement.xml")
    parser.add_argument("--version", "-V", action="version", version=__version__)
    args = parser.parse_args()
    input_file = args.input_file

    statement = BankToCustomerStatement.from_file(input_file)
    print(statement.json(indent=4, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
