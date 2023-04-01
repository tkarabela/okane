[![CI - build](https://img.shields.io/github/actions/workflow/status/tkarabela/okane/main.yml?branch=master)](https://github.com/tkarabela/okane/actions)

# お<ruby>金<rt>かね</rt></ruby> 【okane】

_okane_ is a pure Python parser for bank statements in camt.053 XML format, in dialect
used by the Czech Banking Association (ČBA).

It parses `BkToCstmrStmt` XML element into `okane.BankToCustomerStatement` which is
a Pydantic model.

## Example

```
$ head my_banking_statement.xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
    <BkToCstmrStmt>
        <GrpHdr>
            <MsgId>camt.053-2023-04-01-001</MsgId>
            <CreDtTm>2023-04-01T12:00:00.000+02:00</CreDtTm>
            <MsgRcpt>
                <Nm>John Doe</Nm>

$ ./okane.py my_banking_statement.xml
{                                               
    "statement_id": "XXX-STATEMENT-ID",         
    "created_time": "2023-04-01T12:00:00+02:00",
    "from_time": "2023-03-01T00:00:00+01:00",   
    "to_time": "2023-03-31T00:00:00+02:00",     
    "account_iban": "XXX-IBAN",                 
    "opening_balance": {                        
        "amount": 1000.0,
        "currency": "CZK",
        "date": "2023-03-31"
    },
    "closing_balance": {
        "amount": 2000.0,
        "currency": "CZK",
        "date": "2023-03-31"
    },
    "transactions": [
        {
            "ref": "XXX-REF-1",
            "amount": 1500.0,
            "currency": "CZK",
            "val_date": "2023-04-01",
            "remote_info": "Incoming payment",
            "additional_transaction_info": null,
            "related_account": null,
            "related_account_bank": null
        },
        {
            "ref": "XXX-REF-2",
            "amount": -500.0,
            "currency": "CZK",
            "val_date": "2023-04-01",
            "remote_info": "Outbound payment",
            "additional_transaction_info": null,
            "related_account": null,
            "related_account_bank": null
        }
    ]
}

```


## License

MIT - see [LICENSE.txt](./LICENSE.txt).
