import datetime
from decimal import Decimal

import okane
import pytest

try:
    import polars as pl
except Exception:
    pl = None


def test_1(shared_datadir):
    path = shared_datadir.joinpath("test1.xml")
    statement = okane.BankToCustomerStatement.from_file(path)

    assert statement.account_id == okane.AccountId(iban="XXX-IBAN")
    assert statement.statement_id == "XXX-STATEMENT-ID"
    assert statement.created_time == datetime.datetime(2023, 4, 1, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)))
    assert statement.from_time == datetime.datetime(2023, 3, 1, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=3600)))
    assert statement.to_time == datetime.datetime(2023, 3, 31, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)))

    assert statement.opening_balance.amount == 1000
    assert statement.opening_balance.currency == "CZK"
    assert statement.opening_balance.date == datetime.date(2023, 3, 31)  # I think this should be 2023-03-01 but this is how it appears on the statement...

    assert statement.closing_balance.amount == 2000
    assert statement.closing_balance.currency == "CZK"
    assert statement.closing_balance.date == datetime.date(2023, 3, 31)

    assert len(statement.transactions) == 2

    t1 = statement.transactions[0]
    assert t1.amount == 1500
    assert t1.currency == "CZK"
    assert t1.entry_ref == "XXX-REF-1"
    assert t1.ref == okane.TransactionRef(account_servicer_ref="XXX")
    assert str(t1.ref) == 'account_servicer_ref=XXX'
    assert t1.val_date == datetime.date(2023, 3, 12)
    assert t1.info == 'Incoming payment'

    t2 = statement.transactions[1]
    assert t2.amount == -500
    assert t2.currency == "CZK"
    assert t2.entry_ref == "XXX-REF-2"
    assert t2.val_date == datetime.date(2023, 3, 17)
    assert t2.info == 'Outbound payment'


@pytest.mark.skipif(pl is None, reason="requires polars")
def test_1_balance_df(shared_datadir):
    path = shared_datadir.joinpath("test1.xml")
    statement = okane.BankToCustomerStatement.from_file(path)

    df = statement.get_balance_dataframe()
    assert df["val_date"].to_list() == [
        datetime.date(2023, 3, 1), datetime.date(2023, 3, 2), datetime.date(2023, 3, 3),
        datetime.date(2023, 3, 4), datetime.date(2023, 3, 5), datetime.date(2023, 3, 6),
        datetime.date(2023, 3, 7), datetime.date(2023, 3, 8), datetime.date(2023, 3, 9),
        datetime.date(2023, 3, 10), datetime.date(2023, 3, 11), datetime.date(2023, 3, 12),
        datetime.date(2023, 3, 13), datetime.date(2023, 3, 14), datetime.date(2023, 3, 15),
        datetime.date(2023, 3, 16), datetime.date(2023, 3, 17), datetime.date(2023, 3, 18),
        datetime.date(2023, 3, 19), datetime.date(2023, 3, 20), datetime.date(2023, 3, 21),
        datetime.date(2023, 3, 22), datetime.date(2023, 3, 23), datetime.date(2023, 3, 24),
        datetime.date(2023, 3, 25), datetime.date(2023, 3, 26), datetime.date(2023, 3, 27),
        datetime.date(2023, 3, 28), datetime.date(2023, 3, 29), datetime.date(2023, 3, 30),
        datetime.date(2023, 3, 31)
    ]
    assert df["amount"].to_list() == [
        Decimal('1000.00'), Decimal('1000.00'), Decimal('1000.00'), Decimal('1000.00'),
        Decimal('1000.00'), Decimal('1000.00'), Decimal('1000.00'), Decimal('1000.00'),
        Decimal('1000.00'), Decimal('1000.00'), Decimal('1000.00'), Decimal('2500.00'),
        Decimal('2500.00'), Decimal('2500.00'), Decimal('2500.00'), Decimal('2500.00'),
        Decimal('2000.00'), Decimal('2000.00'), Decimal('2000.00'), Decimal('2000.00'),
        Decimal('2000.00'), Decimal('2000.00'), Decimal('2000.00'), Decimal('2000.00'),
        Decimal('2000.00'), Decimal('2000.00'), Decimal('2000.00'), Decimal('2000.00'),
        Decimal('2000.00'), Decimal('2000.00'), Decimal('2000.00')
    ]
