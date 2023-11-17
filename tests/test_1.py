import os.path as op
import datetime

import okane


def test_1():
    path = op.join(op.dirname(__file__), "./data/test1.xml")

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
    assert t1.ref == "XXX-REF-1"
    assert t1.val_date == datetime.date(2023, 4, 1)
    assert t1.info == 'Incoming payment'

    t2 = statement.transactions[1]
    assert t2.amount == -500
    assert t2.currency == "CZK"
    assert t2.ref == "XXX-REF-2"
    assert t2.val_date == datetime.date(2023, 4, 1)
    assert t2.info == 'Outbound payment'
