-- View: public.double_entry_candidates

-- DROP VIEW public.double_entry_candidates;

CREATE OR REPLACE VIEW public.double_entry_candidates
 AS
 SELECT tj1.id AS tj_id1,
    tj2.id AS tj_id2,
    abs(date_part('day'::text, tj1.date - tj2.date)) AS days_diff,
    tj1.date AS date1,
    tj2.date AS date2,
    tx1.amount,
    acc.name,
    tx1.reconciled AS tx1_reconciled,
    tx2.reconciled AS tx2_reconciled
   FROM transaction_journals tj1
     JOIN transactions tx1 ON tj1.id = tx1.transaction_journal_id
     JOIN transactions tx2 ON tx1.amount = tx2.amount AND tx1.account_id = tx2.account_id AND tx1.id < tx2.id
     JOIN transaction_journals tj2 ON tj2.id = tx2.transaction_journal_id AND abs(date_part('day'::text, tj1.date - tj2.date)) <= 7::double precision
     LEFT JOIN accounts acc ON tx1.account_id = acc.id
  WHERE tx1.id <> tx2.id AND COALESCE(tj1.deleted_at, tx1.deleted_at, tj1.deleted_at, tj2.deleted_at) IS NULL
  ORDER BY tx1.amount;

ALTER TABLE public.double_entry_candidates
    OWNER TO postgres;

