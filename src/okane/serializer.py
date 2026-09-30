from decimal import Decimal
from lxml import etree
from lxml.etree import _Element

from okane.models import BankToCustomerStatement, AccountId, Balance, Transaction, TransactionRef, BankId
from okane.parser import CreditOrDebit

NS = "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"


def _sub(parent: _Element, tag: str, text: str | None = None, **attrib: str) -> _Element:
    e = etree.SubElement(parent, f"{{{NS}}}{tag}", attrib)
    if text is not None:
        e.text = text
    return e


def serialize_statement(statement: BankToCustomerStatement) -> _Element:
    root = etree.Element(f"{{{NS}}}Document", nsmap={None: NS})  # type: ignore[dict-item]
    bk_to_cstmr_stmt = _sub(root, "BkToCstmrStmt")

    grp_hdr = _sub(bk_to_cstmr_stmt, "GrpHdr")
    _sub(grp_hdr, "MsgId", statement.statement_id)
    _sub(grp_hdr, "CreDtTm", statement.created_time.isoformat())

    stmt = _sub(bk_to_cstmr_stmt, "Stmt")
    _sub(stmt, "Id", statement.statement_id)
    _sub(stmt, "CreDtTm", statement.created_time.isoformat())
    fr_to_dt = _sub(stmt, "FrToDt")
    _sub(fr_to_dt, "FrDtTm", statement.from_time.isoformat())
    _sub(fr_to_dt, "ToDtTm", statement.to_time.isoformat())

    acct = _sub(stmt, "Acct")
    serialize_account_id(_sub(acct, "Id"), statement.account_id)

    serialize_balance(_sub(stmt, "Bal"), statement.opening_balance, "PRCD")
    serialize_balance(_sub(stmt, "Bal"), statement.closing_balance, "CLBD")

    for tx in statement.transactions:
        serialize_transaction(_sub(stmt, "Ntry"), tx)

    return root


def serialize_amount(parent: _Element, amount: Decimal, currency: str) -> None:
    _sub(parent, "Amt", format(abs(amount), "f"), Ccy=currency)
    _sub(parent, "CdtDbtInd", CreditOrDebit.DBIT if amount < 0 else CreditOrDebit.CRDT)


def serialize_balance(bal: _Element, balance: Balance, code: str) -> None:
    tp = _sub(bal, "Tp")
    cd_or_prtry = _sub(tp, "CdOrPrtry")
    _sub(cd_or_prtry, "Cd", code)
    serialize_amount(bal, balance.amount, balance.currency)
    dt = _sub(bal, "Dt")
    _sub(dt, "Dt", balance.date.isoformat())


def serialize_account_id(id_: _Element, account_id: AccountId) -> None:
    if account_id.iban is not None:
        _sub(id_, "IBAN", account_id.iban)
    if account_id.id is not None:
        othr = _sub(id_, "Othr")
        _sub(othr, "Id", account_id.id)


def serialize_bank_id(fin_instn_id: _Element, bank_id: BankId) -> None:
    if bank_id.bic is not None:
        _sub(fin_instn_id, "BIC", bank_id.bic)
    if bank_id.id is not None:
        othr = _sub(fin_instn_id, "Othr")
        _sub(othr, "Id", bank_id.id)


def serialize_transaction_ref(tx_dtls: _Element, ref: TransactionRef) -> None:
    fields = [
        ("MsgId", ref.message_id),
        ("AcctSvcrRef", ref.account_servicer_ref),
        ("PmtInfId", ref.payment_invocation_id),
        ("InstrId", ref.instruction_id),
        ("EndToEndId", ref.end_to_end_id),
        ("MndtId", ref.mandate_id),
        ("ChqNb", ref.cheque_number),
        ("ClrSysRef", ref.clearing_system_ref),
    ]
    if all(value is None for _, value in fields):
        return

    refs = _sub(tx_dtls, "Refs")
    for tag, value in fields:
        if value is not None:
            _sub(refs, tag, value)


def serialize_transaction(ntry: _Element, tx: Transaction) -> None:
    _sub(ntry, "NtryRef", tx.entry_ref)
    serialize_amount(ntry, tx.amount, tx.currency)
    _sub(ntry, "Sts", "BOOK")
    val_dt = _sub(ntry, "ValDt")
    _sub(val_dt, "Dt", tx.val_date.isoformat())

    ntry_dtls = _sub(ntry, "NtryDtls")
    tx_dtls = _sub(ntry_dtls, "TxDtls")
    serialize_transaction_ref(tx_dtls, tx.ref)

    # for incoming payment, the related party is the debtor; for outgoing payment, it's the creditor
    related_party = "Dbtr" if tx.amount >= 0 else "Cdtr"

    if tx.related_account_id is not None:
        rltd_pties = _sub(tx_dtls, "RltdPties")
        acct = _sub(rltd_pties, f"{related_party}Acct")
        serialize_account_id(_sub(acct, "Id"), tx.related_account_id)

    if tx.related_account_bank_id is not None:
        rltd_agts = _sub(tx_dtls, "RltdAgts")
        agt = _sub(rltd_agts, f"{related_party}Agt")
        serialize_bank_id(_sub(agt, "FinInstnId"), tx.related_account_bank_id)

    if tx.remote_info is not None:
        rmt_inf = _sub(tx_dtls, "RmtInf")
        _sub(rmt_inf, "Ustrd", tx.remote_info)

    if tx.additional_transaction_info is not None:
        _sub(tx_dtls, "AddtlTxInf", tx.additional_transaction_info)
