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


def test_negative_balance():
    tz = datetime.timezone(datetime.timedelta(hours=1))
    ref = okane.BankToCustomerStatement(
        statement_id="XXX-STATEMENT-ID",
        created_time=datetime.datetime(2023, 4, 1, 12, 0, tzinfo=tz),
        from_time=datetime.datetime(2023, 3, 1, 0, 0, tzinfo=tz),
        to_time=datetime.datetime(2023, 3, 31, 23, 59, 59, 999000, tzinfo=tz),
        account_id=okane.AccountId(id="XXX-ACC"),
        opening_balance=okane.Balance(amount=Decimal("-123.45"), currency="CZK", date=datetime.date(2023, 3, 1)),
        closing_balance=okane.Balance(amount=Decimal("-123.45"), currency="CZK", date=datetime.date(2023, 3, 31)),
        transactions=[],
    )

    raw_xml = ref.to_bytes()
    assert b"<CdtDbtInd>DBIT</CdtDbtInd>" in raw_xml
    assert okane.BankToCustomerStatement.from_bytes(raw_xml) == ref
