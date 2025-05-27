-- View: public.monthly_expenses_billed

-- DROP VIEW public.monthly_expenses_billed;

CREATE OR REPLACE VIEW public.monthly_expenses_billed
 AS
 SELECT all_dates.yr_mth,
    with_bills.count AS bill_tx_num,
    with_bills.sum AS bill_amt,
    wo_bills.sum AS wob_amt,
    wo_bills.count AS wob_tx_num
   FROM ( SELECT DISTINCT date_trunc('month'::text, txj.date) AS yr_mth
           FROM transaction_journals txj) all_dates
     LEFT JOIN ( SELECT date_trunc('month'::text, txj.date) AS mth,
            sum(tx.amount) AS sum,
            count(*) AS count
           FROM accounts accs
             JOIN account_types acctys ON acctys.id = accs.account_type_id
             JOIN transactions tx ON accs.id = tx.account_id
             JOIN transaction_journals txj ON tx.transaction_journal_id = txj.id
          WHERE acctys.type::text ~~ '%Expense%'::text AND tx.deleted_at IS NULL AND txj.bill_id IS NOT NULL
          GROUP BY (date_trunc('month'::text, txj.date))) with_bills ON all_dates.yr_mth = with_bills.mth
     LEFT JOIN ( SELECT date_trunc('month'::text, txj.date) AS mth,
            sum(tx.amount) AS sum,
            count(*) AS count
           FROM accounts accs
             JOIN account_types acctys ON acctys.id = accs.account_type_id
             JOIN transactions tx ON accs.id = tx.account_id
             JOIN transaction_journals txj ON tx.transaction_journal_id = txj.id
          WHERE acctys.type::text ~~ '%Expense%'::text AND tx.deleted_at IS NULL AND txj.bill_id IS NULL
          GROUP BY (date_trunc('month'::text, txj.date))) wo_bills ON all_dates.yr_mth = wo_bills.mth
  ORDER BY all_dates.yr_mth DESC;

ALTER TABLE public.monthly_expenses_billed
    OWNER TO postgres;

