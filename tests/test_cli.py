import os.path as op
import json
from io import StringIO, BytesIO
import pytest
import okane
try:
    import pandas as pd
except Exception:
    pd = None


def test_cli_to_json(capsys):
    path = op.join(op.dirname(__file__), "./data/test2.xml")

    assert 0 == okane.main([path])

    output = capsys.readouterr().out
    output_dict = json.loads(output)

    assert output_dict == TEST2_REFERENCE_DICT


def test_cli_to_json_multiple(capsys):
    path1 = op.join(op.dirname(__file__), "./data/test1.xml")
    path2 = op.join(op.dirname(__file__), "./data/test2.xml")

    assert 0 == okane.main([path1, path2, "--no-indent"])
    output = capsys.readouterr().out
    output_lines = output.splitlines()
    output_dict1 = json.loads(output_lines[0])
    output_dict2 = json.loads(output_lines[1])

    assert output_dict1 == TEST1_REFERENCE_DICT
    assert output_dict2 == TEST2_REFERENCE_DICT


@pytest.mark.skipif(pd is None, reason="requires pandas")
def test_cli_to_csv_multiple(capsys):
    path1 = op.join(op.dirname(__file__), "./data/test1.xml")
    path2 = op.join(op.dirname(__file__), "./data/test2.xml")

    statement1 = okane.BankToCustomerStatement.from_file(path1)
    statement2 = okane.BankToCustomerStatement.from_file(path2)
    df_ref = pd.concat(s.as_dataframe() for s in [statement1, statement2])

    assert 0 == okane.main([path1, path2, "-f", "csv"])

    output = capsys.readouterr().out
    buf = StringIO(output)
    df = pd.read_csv(buf)

    df_ = df.where(pd.notnull(df), None).reset_index().map(str)
    df_ref_ = df_ref.where(pd.notnull(df_ref), None).reset_index().map(str)

    assert (df_["statement.id"] == df_ref_["statement.id"]).all()
    assert (df_["transaction.entry_ref"] == df_ref_["transaction.entry_ref"]).all()
    assert (df_["transaction.val_date"] == df_ref_["transaction.val_date"]).all()
    # TODO compare more thoroughly


@pytest.mark.skipif(pd is None, reason="requires pandas")
def test_cli_to_excel_multiple(capsysbinary):
    path1 = op.join(op.dirname(__file__), "./data/test1.xml")
    path2 = op.join(op.dirname(__file__), "./data/test2.xml")

    statement1 = okane.BankToCustomerStatement.from_file(path1)
    statement2 = okane.BankToCustomerStatement.from_file(path2)
    df_ref = pd.concat(s.as_dataframe() for s in [statement1, statement2])


    assert 0 == okane.main([path1, path2, "-f", "xlsx"])

    output = capsysbinary.readouterr().out
    buf = BytesIO(output)
    df = pd.read_excel(buf)

    df_ = df.where(pd.notnull(df), None).reset_index().map(str)
    df_ref_ = df_ref.where(pd.notnull(df_ref), None).reset_index().map(str)

    assert (df_["statement.id"] == df_ref_["statement.id"]).all()
    assert (df_["transaction.entry_ref"] == df_ref_["transaction.entry_ref"]).all()
    # TODO compare more thoroughly


TEST1_REFERENCE_DICT = {'account_id': {'iban': 'XXX-IBAN', 'id': None},
 'closing_balance': {'amount': '2000.00',
                     'currency': 'CZK',
                     'date': '2023-03-31'},
 'created_time': '2023-04-01T12:00:00+02:00',
 'from_time': '2023-03-01T00:00:00+01:00',
 'opening_balance': {'amount': '1000.00',
                     'currency': 'CZK',
                     'date': '2023-03-31'},
 'statement_id': 'XXX-STATEMENT-ID',
 'to_time': '2023-03-31T00:00:00+02:00',
 'transactions': [{'additional_transaction_info': None,
                   'amount': '1500.00',
                   'currency': 'CZK',
                   'entry_ref': 'XXX-REF-1',
                   'ref': {'account_servicer_ref': 'XXX',
                           'cheque_number': None,
                           'clearing_system_ref': None,
                           'end_to_end_id': None,
                           'instruction_id': None,
                           'mandate_id': None,
                           'message_id': None,
                           'payment_invocation_id': None},
                   'related_account_bank_id': None,
                   'related_account_id': None,
                   'remote_info': 'Incoming payment',
                   'val_date': '2023-04-01'},
                  {'additional_transaction_info': None,
                   'amount': '-500.00',
                   'currency': 'CZK',
                   'entry_ref': 'XXX-REF-2',
                   'ref': {'account_servicer_ref': 'XXX',
                           'cheque_number': None,
                           'clearing_system_ref': None,
                           'end_to_end_id': None,
                           'instruction_id': None,
                           'mandate_id': None,
                           'message_id': None,
                           'payment_invocation_id': None},
                   'related_account_bank_id': None,
                   'related_account_id': None,
                   'remote_info': 'Outbound payment',
                   'val_date': '2023-04-01'}]}

TEST2_REFERENCE_DICT = {'account_id': {'iban': 'XXX-IBAN', 'id': None},
 'closing_balance': {'amount': '2000.00',
                     'currency': 'CZK',
                     'date': '2023-03-31'},
 'created_time': '2023-04-01T12:00:00+02:00',
 'from_time': '2023-03-01T00:00:00+01:00',
 'opening_balance': {'amount': '1000.00',
                     'currency': 'CZK',
                     'date': '2023-03-01'},
 'statement_id': 'XXX-STATEMENT-ID',
 'to_time': '2023-03-31T23:59:59.999000+02:00',
 'transactions': [{'additional_transaction_info': 'Nákup dne 27.2.2023, částka '
                                                  '100.00 CZK',
                   'amount': '-100.00',
                   'currency': 'CZK',
                   'entry_ref': 'XXX-REF-1',
                   'ref': {'account_servicer_ref': None,
                           'cheque_number': None,
                           'clearing_system_ref': None,
                           'end_to_end_id': 'XXX',
                           'instruction_id': None,
                           'mandate_id': None,
                           'message_id': 'XXX',
                           'payment_invocation_id': None},
                   'related_account_bank_id': None,
                   'related_account_id': None,
                   'remote_info': 'Nákup dne 27.2.2023, částka 100.00 CZK',
                   'val_date': '2023-03-01'},
                  {'additional_transaction_info': 'transaction note',
                   'amount': '-200.00',
                   'currency': 'CZK',
                   'entry_ref': 'XXX-REF-2',
                   'ref': {'account_servicer_ref': None,
                           'cheque_number': None,
                           'clearing_system_ref': None,
                           'end_to_end_id': 'XXX',
                           'instruction_id': None,
                           'mandate_id': None,
                           'message_id': 'XXX',
                           'payment_invocation_id': None},
                   'related_account_bank_id': {'bic': None,
                                               'id': 'XXX-OTHER-BANK'},
                   'related_account_id': {'iban': None, 'id': 'XXX-OTHER-ACC'},
                   'remote_info': None,
                   'val_date': '2023-03-02'},
                  {'additional_transaction_info': None,
                   'amount': '1000.00',
                   'currency': 'CZK',
                   'entry_ref': 'XXX-REF-3',
                   'ref': {'account_servicer_ref': None,
                           'cheque_number': None,
                           'clearing_system_ref': None,
                           'end_to_end_id': None,
                           'instruction_id': None,
                           'mandate_id': None,
                           'message_id': 'XXX',
                           'payment_invocation_id': None},
                   'related_account_bank_id': {'bic': None,
                                               'id': 'XXX-OTHER-BANK'},
                   'related_account_id': {'iban': None, 'id': 'XXX-OTHER-ACC'},
                   'remote_info': None,
                   'val_date': '2023-03-07'},
                  {'additional_transaction_info': 'RECIPIENT NAME',
                   'amount': '400.00',
                   'currency': 'CZK',
                   'entry_ref': 'XXX-REF-4',
                   'ref': {'account_servicer_ref': None,
                           'cheque_number': None,
                           'clearing_system_ref': None,
                           'end_to_end_id': 'XXX',
                           'instruction_id': None,
                           'mandate_id': None,
                           'message_id': 'XXX',
                           'payment_invocation_id': None},
                   'related_account_bank_id': {'bic': None,
                                               'id': 'XXX-OTHER-BANK'},
                   'related_account_id': {'iban': None, 'id': 'XXX-OTHER-ACC'},
                   'remote_info': 'description',
                   'val_date': '2023-03-08'},
                  {'additional_transaction_info': None,
                   'amount': '-100.00',
                   'currency': 'CZK',
                   'entry_ref': 'XXX-REF-5',
                   'ref': {'account_servicer_ref': None,
                           'cheque_number': None,
                           'clearing_system_ref': None,
                           'end_to_end_id': 'XXX',
                           'instruction_id': None,
                           'mandate_id': None,
                           'message_id': 'XXX',
                           'payment_invocation_id': None},
                   'related_account_bank_id': None,
                   'related_account_id': None,
                   'remote_info': 'transaction description',
                   'val_date': '2023-03-31'},
                  {'additional_transaction_info': None,
                   'amount': '1000.00',
                   'currency': 'CZK',
                   'entry_ref': 'XXX-REF-6',
                   'ref': {'account_servicer_ref': None,
                           'cheque_number': None,
                           'clearing_system_ref': None,
                           'end_to_end_id': None,
                           'instruction_id': None,
                           'mandate_id': None,
                           'message_id': 'XXX',
                           'payment_invocation_id': None},
                   'related_account_bank_id': {'bic': 'REVOLT21', 'id': None},
                   'related_account_id': {'iban': 'LT6632xxxxxx', 'id': None},
                   'remote_info': None,
                   'val_date': '2023-03-07'}]}
