-- View: public.expense_detail

-- DROP VIEW public.expense_detail;

CREATE OR REPLACE VIEW public.expense_detail
 AS
 SELECT txj.date,
    tx.amount,
    txj.id AS tx_journal_id,
    acc.name AS expense_account,
    non_expense_acc.name AS paid_from_acc,
    cats.name AS category_name,
    txj.description,
    txj.bill_id,
    acc.id AS expense_account_id,
    non_expense_acc.id AS paid_from_account_id
   FROM transactions tx
     JOIN transaction_journals txj ON tx.transaction_journal_id = txj.id
     JOIN transactions tx_non_expense ON tx_non_expense.transaction_journal_id = txj.id AND tx_non_expense.id <> tx.id
     JOIN accounts acc ON tx.account_id = acc.id
     JOIN account_types acctypes ON acc.account_type_id = acctypes.id
     JOIN accounts non_expense_acc ON non_expense_acc.id = tx_non_expense.account_id
     LEFT JOIN category_transaction_journal ctj ON ctj.transaction_journal_id = txj.id
     LEFT JOIN categories cats ON ctj.category_id = cats.id
  WHERE acctypes.type::text ~~ 'Expense%'::text AND txj.deleted_at IS NULL AND tx.deleted_at IS NULL AND acc.deleted_at IS NULL
  ORDER BY txj.date DESC;

ALTER TABLE public.expense_detail
    OWNER TO postgres;

