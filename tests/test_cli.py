import os.path as op
import json
import okane


def test_cli(capsys):
    path = op.join(op.dirname(__file__), "./data/test2.xml")

    assert 0 == okane.main([path])

    output_dict_reference = {
        "statement_id": "XXX-STATEMENT-ID",
        "created_time": "2023-04-01T12:00:00+02:00",
        "from_time": "2023-03-01T00:00:00+01:00",
        "to_time": "2023-03-31T23:59:59.999000+02:00",
        "account_iban": "XXX-IBAN",
        "opening_balance": {
            "amount": "1000.00",
            "currency": "CZK",
            "date": "2023-03-01"
        },
        "closing_balance": {
            "amount": "2000.00",
            "currency": "CZK",
            "date": "2023-03-31"
        },
        "transactions": [
            {
                "ref": "XXX-REF-1",
                "amount": "-100.00",
                "currency": "CZK",
                "val_date": "2023-03-01",
                "remote_info": "Nákup dne 27.2.2023, částka 100.00 CZK\n                            ",
                "additional_transaction_info": "Nákup dne 27.2.2023, částka 100.00 CZK\n                        ",
                "related_account": None,
                "related_account_bank": None
            },
            {
                "ref": "XXX-REF-2",
                "amount": "-200.00",
                "currency": "CZK",
                "val_date": "2023-03-02",
                "remote_info": None,
                "additional_transaction_info": "transaction note",
                "related_account": "XXX-OTHER-ACC",
                "related_account_bank": "XXX-OTHER-BANK"
            },
            {
                "ref": "XXX-REF-3",
                "amount": "1000.00",
                "currency": "CZK",
                "val_date": "2023-03-07",
                "remote_info": None,
                "additional_transaction_info": None,
                "related_account": "XXX-OTHER-ACC",
                "related_account_bank": "XXX-OTHER-BANK"
            },
            {
                "ref": "XXX-REF-4",
                "amount": "400.00",
                "currency": "CZK",
                "val_date": "2023-03-08",
                "remote_info": "description",
                "additional_transaction_info": "RECIPIENT NAME",
                "related_account": "XXX-OTHER-ACC",
                "related_account_bank": "XXX-OTHER-BANK"
            },
            {
                "ref": "XXX-REF-5",
                "amount": "-100.00",
                "currency": "CZK",
                "val_date": "2023-03-31",
                "remote_info": "transaction description",
                "additional_transaction_info": None,
                "related_account": None,
                "related_account_bank": None
            }
        ]
    }

    output = capsys.readouterr().out
    output_dict = json.loads(output)

    assert output_dict == output_dict_reference
