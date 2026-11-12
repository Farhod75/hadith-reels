-- P409 (Sol R5): bind matn_verified_at to the text it approved.
--
-- matn_verified_at means "a human read this row's matn and translations against a
-- source" (P151, P265). It was a bare timestamp: edit text_russian a month later and
-- the row still said verified. Now:
--   * matn_verified_sha256 holds a hash of the five columns Stage 3 / Stage 4 read
--     (text_arabic, text_english, text_russian, text_uzbek_cyrillic, text_tajik),
--     computed by the database whenever matn_verified_at is set;
--   * an UPDATE that changes any of those five columns WITHOUT setting
--     matn_verified_at in the same statement clears both - the approval does not
--     carry over to text nobody approved. Setting matn_verified_at = now() in the
--     same UPDATE as a corrected text is how a re-read is recorded.
--
-- Run once in the Supabase SQL editor. Safe to re-run.

alter table public.hadith_library
  add column if not exists matn_verified_sha256 text;

create or replace function public.hadith_matn_hash(r public.hadith_library)
returns text language sql immutable as $$
  select encode(sha256(convert_to(
           coalesce(r.text_arabic, '')         || chr(31) ||
           coalesce(r.text_english, '')        || chr(31) ||
           coalesce(r.text_russian, '')        || chr(31) ||
           coalesce(r.text_uzbek_cyrillic, '') || chr(31) ||
           coalesce(r.text_tajik, ''), 'UTF8')), 'hex')
$$;

create or replace function public.hadith_matn_verified_binding()
returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE'
     and new.matn_verified_at is not distinct from old.matn_verified_at
     and (new.text_arabic         is distinct from old.text_arabic
       or new.text_english        is distinct from old.text_english
       or new.text_russian        is distinct from old.text_russian
       or new.text_uzbek_cyrillic is distinct from old.text_uzbek_cyrillic
       or new.text_tajik          is distinct from old.text_tajik) then
    new.matn_verified_at := null;               -- text changed, nobody re-read it
  end if;
  new.matn_verified_sha256 := case when new.matn_verified_at is null then null
                                   else public.hadith_matn_hash(new) end;
  return new;
end
$$;

drop trigger if exists hadith_matn_verified_binding on public.hadith_library;
create trigger hadith_matn_verified_binding
  before insert or update on public.hadith_library
  for each row execute function public.hadith_matn_verified_binding();

-- Baseline: rows verified before today get the hash of their CURRENT text. That
-- records what is verified as of 2026-11-12; it cannot prove the text never moved
-- before the trigger existed (see fix_patterns P409).
update public.hadith_library
   set matn_verified_sha256 = public.hadith_matn_hash(hadith_library)
 where matn_verified_at is not null;

-- Check (read the result): every verified row has a hash; none without.
select count(*) filter (where matn_verified_at is not null)                              as verified,
       count(*) filter (where matn_verified_at is not null and matn_verified_sha256 is null) as verified_without_hash,
       count(*) filter (where matn_verified_at is null and matn_verified_sha256 is not null) as hash_without_verified
  from public.hadith_library;
