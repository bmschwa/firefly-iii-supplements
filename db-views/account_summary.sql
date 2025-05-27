-- View: public.account_summary

-- DROP VIEW public.account_summary;

CREATE OR REPLACE VIEW public.account_summary
 AS
 SELECT acc.id,
    acc.active,
    acc.name,
    acctypes.type,
    acc.updated_at AS account_update_time,
    tx_summary.tx_updated_max,
    tx_summary.tx_amount_sum,
    tx_summary.tx_n
   FROM accounts acc
     JOIN account_types acctypes ON acc.account_type_id = acctypes.id
     FULL JOIN ( SELECT tx.account_id,
            count(tx.id) AS tx_n,
            max(tx.updated_at) AS tx_updated_max,
            sum(tx.amount) AS tx_amount_sum
           FROM transactions tx
          WHERE tx.deleted_at IS NULL
          GROUP BY tx.account_id) tx_summary ON tx_summary.account_id = acc.id
  WHERE acc.deleted_at IS NULL
  ORDER BY acctypes.type, acc.name;

ALTER TABLE public.account_summary
    OWNER TO postgres;

