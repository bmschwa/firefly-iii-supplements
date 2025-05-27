-- View: public.expenses_with_category

-- DROP VIEW public.expenses_with_category;

CREATE OR REPLACE VIEW public.expenses_with_category
 AS
 SELECT tg.id AS tg_id,
    tj.transaction_type_id,
    tj.date,
    cs.name AS category_name,
    acc.name AS acct_name,
    acc.id AS account_id,
    tx.amount,
    tj.description
   FROM transaction_journals tj
     JOIN transactions tx ON tj.id = tx.transaction_journal_id
     JOIN transaction_groups tg ON tj.transaction_group_id = tg.id
     LEFT JOIN category_transaction_journal ctj ON ctj.transaction_journal_id = tj.id
     LEFT JOIN categories cs ON cs.id = ctj.category_id
     LEFT JOIN accounts acc ON tx.account_id = acc.id
     JOIN account_types accts ON acc.account_type_id = accts.id
  WHERE (tj.transaction_type_id = ANY (ARRAY[1, 3])) AND acc.account_type_id = 4 AND tg.deleted_at IS NULL;

ALTER TABLE public.expenses_with_category
    OWNER TO postgres;

