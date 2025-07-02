Plaid has an extensive API.  It has been configured to use for [firefly-iii-connector2](https://github.com/dvankley/firefly-plaid-connector-2).  

My Firefly-iii instance is terribly out of whack.   Going to try to set up some code in order to figure out what's up

https://plaid.com/docs/api/accounts/#accountsget

https://plaid.com/docs/api/products/balance/#accountsbalanceget

https://plaid.com/docs/api/oauth/#oauthintrospect

https://plaid.com/docs/api/products/statements/#statementslist

https://plaid.com/docs/api/products/liabilities/#liabilitiesget


https://plaid.com/docs/api/institutions/#institutionsget_by_id


Pandas:

- account inst & ids
- firefly 
  - last transaction date
  - balance
  - n transaction
- plaid 
  - balances
  - due dates & amounts
  - rates??