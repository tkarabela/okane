import os.path as op
import json
import okane


def test_cli(capsys):
    path = op.join(op.dirname(__file__), "./data/test2.xml")

    assert 0 == okane.main([path])

    output_dict_reference = {
        'account_id': {'iban': 'XXX-IBAN', 'id': None},
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
        'transactions': [{'additional_transaction_info': 'Nákup dne 27.2.2023, částka 100.00 CZK',
                          'amount': '-100.00',
                          'currency': 'CZK',
                          'ref': 'XXX-REF-1',
                          'related_account_bank_id': None,
                          'related_account_id': None,
                          'remote_info': 'Nákup dne 27.2.2023, částka 100.00 CZK',
                          'val_date': '2023-03-01'},
                         {'additional_transaction_info': 'transaction note',
                          'amount': '-200.00',
                          'currency': 'CZK',
                          'ref': 'XXX-REF-2',
                          'related_account_bank_id': {'bic': None,
                                                      'id': 'XXX-OTHER-BANK'},
                          'related_account_id': {'iban': None, 'id': 'XXX-OTHER-ACC'},
                          'remote_info': None,
                          'val_date': '2023-03-02'},
                         {'additional_transaction_info': None,
                          'amount': '1000.00',
                          'currency': 'CZK',
                          'ref': 'XXX-REF-3',
                          'related_account_bank_id': {'bic': None,
                                                      'id': 'XXX-OTHER-BANK'},
                          'related_account_id': {'iban': None, 'id': 'XXX-OTHER-ACC'},
                          'remote_info': None,
                          'val_date': '2023-03-07'},
                         {'additional_transaction_info': 'RECIPIENT NAME',
                          'amount': '400.00',
                          'currency': 'CZK',
                          'ref': 'XXX-REF-4',
                          'related_account_bank_id': {'bic': None,
                                                      'id': 'XXX-OTHER-BANK'},
                          'related_account_id': {'iban': None, 'id': 'XXX-OTHER-ACC'},
                          'remote_info': 'description',
                          'val_date': '2023-03-08'},
                         {'additional_transaction_info': None,
                          'amount': '-100.00',
                          'currency': 'CZK',
                          'ref': 'XXX-REF-5',
                          'related_account_bank_id': None,
                          'related_account_id': None,
                          'remote_info': 'transaction description',
                          'val_date': '2023-03-31'},
                         {'additional_transaction_info': None,
                          'amount': '1000.00',
                          'currency': 'CZK',
                          'ref': 'XXX-REF-6',
                          'related_account_bank_id': {'bic': 'REVOLT21', 'id': None},
                          'related_account_id': {'iban': 'LT6632xxxxxx', 'id': None},
                          'remote_info': None,
                          'val_date': '2023-03-07'}]}

    output = capsys.readouterr().out
    output_dict = json.loads(output)

    assert output_dict == output_dict_reference
