-- View: public.current_last_month_spend

-- DROP VIEW public.current_last_month_spend;

CREATE OR REPLACE VIEW public.current_last_month_spend
 AS
 WITH current_month AS (
         SELECT date_trunc('month'::text, txj.date) AS mth_yr,
            accs_1.id AS account_id,
            count(*) AS n,
            sum(tx.amount) AS amt
           FROM accounts accs_1
             JOIN account_types acctys ON acctys.id = accs_1.account_type_id
             JOIN transactions tx ON accs_1.id = tx.account_id
             JOIN transaction_journals txj ON tx.transaction_journal_id = txj.id
          WHERE acctys.type::text ~~ '%Expense%'::text AND tx.deleted_at IS NULL
          GROUP BY (date_trunc('month'::text, txj.date)), accs_1.id
         HAVING date_trunc('month'::text, txj.date) = date_trunc('month'::text, now())
        ), last_month AS (
         SELECT date_trunc('month'::text, txj.date) AS mth_yr,
            accs_1.id AS account_id,
            count(*) AS n,
            sum(tx.amount) AS amt
           FROM accounts accs_1
             JOIN account_types acctys ON acctys.id = accs_1.account_type_id
             JOIN transactions tx ON accs_1.id = tx.account_id
             JOIN transaction_journals txj ON tx.transaction_journal_id = txj.id
          WHERE acctys.type::text ~~ '%Expense%'::text AND tx.deleted_at IS NULL AND ((( SELECT current_month_1.mth_yr
                   FROM current_month current_month_1
                 LIMIT 1)) - '1 mon'::interval) = date_trunc('month'::text, txj.date)
          GROUP BY (date_trunc('month'::text, txj.date)), accs_1.id
        )
 SELECT accs.name,
    used_accounts.account_id,
    current_month.amt AS current_month_spend,
    last_month.amt AS last_month_spend
   FROM ( SELECT current_month_1.account_id
           FROM current_month current_month_1
        UNION
         SELECT account_name.account_id
           FROM last_month account_name) used_accounts
     FULL JOIN current_month ON current_month.account_id = used_accounts.account_id
     FULL JOIN last_month ON last_month.account_id = used_accounts.account_id
     JOIN accounts accs ON accs.id = used_accounts.account_id
  ORDER BY accs.name;

ALTER TABLE public.current_last_month_spend
    OWNER TO postgres;

