-- P413: bind matn_screened_at to the Arabic it screened (the "stale screening stamps"
-- TODO under P265, same defect as P409).
--
-- matn_screened_at means: audit-diacritics found this row's text_arabic EXACT against
-- the mirror (P265). Screening reads the Arabic only. A later UPDATE of text_arabic left
-- the stamp attesting to a string that was gone - #8, #1520 and #1894 carried a Sept 5
-- stamp for Arabic replaced that morning. Now:
--   * matn_screened_sha256 = SHA-256 of text_arabic, set by the database whenever
--     matn_screened_at is set;
--   * an UPDATE that changes text_arabic WITHOUT setting matn_screened_at in the same
--     statement clears both. A translation-only change leaves the stamp alone (P265:
--     translate-candidates must not clear it).
--
-- Run once in the Supabase SQL editor. Safe to re-run.

alter table public.hadith_library
  add column if not exists matn_screened_sha256 text;

create or replace function public.hadith_matn_screened_binding()
returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE'
     and new.matn_screened_at is not distinct from old.matn_screened_at
     and new.text_arabic is distinct from old.text_arabic then
    new.matn_screened_at := null;               -- the Arabic changed, nobody re-screened it
  end if;
  new.matn_screened_sha256 := case when new.matn_screened_at is null then null
                                   else encode(sha256(convert_to(coalesce(new.text_arabic, ''), 'UTF8')), 'hex') end;
  return new;
end
$$;

drop trigger if exists hadith_matn_screened_binding on public.hadith_library;
create trigger hadith_matn_screened_binding
  before insert or update on public.hadith_library
  for each row execute function public.hadith_matn_screened_binding();

-- Baseline: rows screened before today get the hash of their CURRENT Arabic (fires the
-- trigger, which computes it). It records the state from 2026-11-12 on.
update public.hadith_library set matn_screened_at = matn_screened_at
 where matn_screened_at is not null;

-- Check (read the result): screened 51, screened_without_hash 0, hash_without_screened 0.
select count(*) filter (where matn_screened_at is not null)                               as screened,
       count(*) filter (where matn_screened_at is not null and matn_screened_sha256 is null) as screened_without_hash,
       count(*) filter (where matn_screened_at is null and matn_screened_sha256 is not null) as hash_without_screened
  from public.hadith_library;
