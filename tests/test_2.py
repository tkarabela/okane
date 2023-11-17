import os.path as op
import datetime

import okane


def test_2():
    path = op.join(op.dirname(__file__), "./data/test2.xml")

    statement = okane.BankToCustomerStatement.from_file(path)

    assert statement.account_id == okane.AccountId(iban="XXX-IBAN")
    assert statement.statement_id == "XXX-STATEMENT-ID"
    assert statement.created_time == datetime.datetime(2023, 4, 1, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)))
    assert statement.from_time == datetime.datetime(2023, 3, 1, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=3600)))
    assert statement.to_time == datetime.datetime(2023, 3, 31, 23, 59, 59, 999000, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)))

    assert statement.opening_balance.amount == 1000
    assert statement.opening_balance.currency == "CZK"
    assert statement.opening_balance.date == datetime.date(2023, 3, 1)

    assert statement.closing_balance.amount == 2000
    assert statement.closing_balance.currency == "CZK"
    assert statement.closing_balance.date == datetime.date(2023, 3, 31)

    assert len(statement.transactions) == 6

    t1 = statement.transactions[0]
    assert t1.amount == -100
    assert t1.currency == "CZK"
    assert t1.ref == "XXX-REF-1"
    assert t1.val_date == datetime.date(2023, 3, 1)
    assert t1.info == 'Nákup dne 27.2.2023, částka 100.00 CZK'

    t2 = statement.transactions[1]
    assert t2.amount == -200
    assert t2.currency == "CZK"
    assert t2.ref == "XXX-REF-2"
    assert t2.val_date == datetime.date(2023, 3, 2)
    assert t2.info == 'transaction note'

    t3 = statement.transactions[2]
    assert t3.amount == 1000
    assert t3.currency == "CZK"
    assert t3.ref == "XXX-REF-3"
    assert t3.val_date == datetime.date(2023, 3, 7)
    assert t3.info == ""
    assert t3.related_account_id == okane.AccountId(id='XXX-OTHER-ACC')
    assert t3.related_account_bank_id == okane.BankId(id='XXX-OTHER-BANK')
    assert t3.related_account == "XXX-OTHER-ACC/XXX-OTHER-BANK"

    t4 = statement.transactions[3]
    assert t4.amount == 400
    assert t4.currency == "CZK"
    assert t4.ref == "XXX-REF-4"
    assert t4.val_date == datetime.date(2023, 3, 8)
    assert t4.info == 'description / RECIPIENT NAME'
    assert t4.related_account_id == okane.AccountId(id='XXX-OTHER-ACC')
    assert t4.related_account_bank_id == okane.BankId(id='XXX-OTHER-BANK')

    t5 = statement.transactions[4]
    assert t5.amount == -100
    assert t5.currency == "CZK"
    assert t5.ref == "XXX-REF-5"
    assert t5.val_date == datetime.date(2023, 3, 31)
    assert t5.info == 'transaction description'

    t6 = statement.transactions[5]
    assert t6.amount == 1000
    assert t6.currency == "CZK"
    assert t6.ref == "XXX-REF-6"
    assert t6.val_date == datetime.date(2023, 3, 7)
    assert t6.info == ""
    assert t6.related_account_id == okane.AccountId(iban='LT6632xxxxxx')
    assert t6.related_account_bank_id == okane.BankId(bic='REVOLT21')
