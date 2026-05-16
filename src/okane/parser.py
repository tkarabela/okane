from decimal import Decimal
from enum import StrEnum
from lxml.etree import _Element
import datetime

from okane.helpers import get_element, get_text, parse_date_isoformat, get_attribute, get_text_or_none
from okane.models import BankToCustomerStatement, AccountId, Balance, Transaction, TransactionRef, BankId


class CreditOrDebit(StrEnum):
    """CreditDebitCode per camt.053"""
    CRDT = "CRDT"
    DBIT = "DBIT"


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
