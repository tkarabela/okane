import datetime
from decimal import Decimal

import okane
import pytest


@pytest.mark.parametrize("name", ["test1.xml", "test2.xml"])
def test_roundtrip_file(shared_datadir, tmp_path, name):
    ref = okane.BankToCustomerStatement.from_file(shared_datadir.joinpath(name))

    output_path = tmp_path / "output.xml"
    ref.to_file(output_path)

    assert okane.BankToCustomerStatement.from_file(output_path) == ref


@pytest.mark.parametrize("name", ["test1.xml", "test2.xml"])
def test_roundtrip_bytes(shared_datadir, name):
    ref = okane.BankToCustomerStatement.from_file(shared_datadir.joinpath(name))

    raw_xml = ref.to_bytes()
    statement = okane.BankToCustomerStatement.from_bytes(raw_xml)

    assert statement == ref
    assert statement.to_bytes() == raw_xml


def test_to_file_matches_to_bytes(shared_datadir, tmp_path):
    ref = okane.BankToCustomerStatement.from_file(shared_datadir.joinpath("test2.xml"))

    output_path = tmp_path / "output.xml"
    ref.to_file(output_path)

    assert output_path.read_bytes() == ref.to_bytes()


def make_statement(transactions=()):
    tz = datetime.timezone(datetime.timedelta(hours=1))
    return okane.BankToCustomerStatement(
        statement_id="XXX-STATEMENT-ID",
        created_time=datetime.datetime(2023, 4, 1, 12, 0, tzinfo=tz),
        from_time=datetime.datetime(2023, 3, 1, 0, 0, tzinfo=tz),
        to_time=datetime.datetime(2023, 3, 31, 23, 59, 59, 999000, tzinfo=tz),
        account_id=okane.AccountId(id="XXX-ACC"),
        opening_balance=okane.Balance(amount=Decimal("-123.45"), currency="CZK", date=datetime.date(2023, 3, 1)),
        closing_balance=okane.Balance(amount=Decimal("-123.45"), currency="CZK", date=datetime.date(2023, 3, 31)),
        transactions=list(transactions),
    )


def make_transaction(bank_transaction_code):
    return okane.Transaction(
        ref=okane.TransactionRef(),
        entry_ref="XXX-REF-1",
        amount=Decimal("100.00"),
        currency="CZK",
        val_date=datetime.date(2023, 3, 1),
        remote_info=None,
        additional_transaction_info=None,
        related_account_id=None,
        related_account_bank_id=None,
        bank_transaction_code=bank_transaction_code,
    )


def test_negative_balance():
    ref = make_statement()

    raw_xml = ref.to_bytes()
    assert b"<CdtDbtInd>DBIT</CdtDbtInd>" in raw_xml
    assert okane.BankToCustomerStatement.from_bytes(raw_xml) == ref


@pytest.mark.parametrize("bank_transaction_code", [
    None,
    okane.BankTransactionCode(proprietary_code="10000405000", proprietary_issuer="CBA"),
    okane.BankTransactionCode(domain_code="PMNT", family_code="RCDT", sub_family_code="ESCT"),
    okane.BankTransactionCode(domain_code="PMNT", family_code="RCDT", sub_family_code="ESCT",
                              proprietary_code="10000405000", proprietary_issuer="CBA"),
])
def test_roundtrip_bank_transaction_code(bank_transaction_code):
    ref = make_statement([make_transaction(bank_transaction_code)])

    raw_xml = ref.to_bytes()
    statement = okane.BankToCustomerStatement.from_bytes(raw_xml)

    assert statement == ref
    assert statement.transactions[0].bank_transaction_code == bank_transaction_code
    if bank_transaction_code is None:
        assert b"<BkTxCd/>" in raw_xml  # BkTxCd is mandatory
