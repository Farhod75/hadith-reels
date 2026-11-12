-- P410 (Sol R10): promotion as ONE transaction.
--
-- promote-candidates.py made three REST writes: insert into hadith_library, insert
-- into hadith_promotions, then stamp the candidate 'promoted'. A failure between them
-- left a library row with no audit trail, and a candidate still 'approved' that the
-- next run inserted again - a duplicate hadith. This function does all three or
-- nothing, locks the candidate row, and refuses a candidate that is not 'approved' or
-- is already promoted.
--
-- Run once in the Supabase SQL editor. Safe to re-run.

create or replace function public.promote_candidate(
  p_candidate_id uuid,
  p_row          jsonb,
  p_reviewer     text,
  p_deeplink     text,
  p_columns      text[]
) returns text
language plpgsql
set search_path = public
as $$
declare
  v_status text;
  v_lib    text;
  v_cols   text;
  v_id     text;
begin
  select status, promoted_library_id into v_status, v_lib
    from hadith_candidates
   where candidate_id = p_candidate_id
     for update;                                   -- a second run waits here, then refuses
  if not found then
    raise exception 'P410: candidate % not found', p_candidate_id;
  end if;
  if v_status is distinct from 'approved' or v_lib is not null then
    raise exception 'P410: candidate % is % (library %) - not promoted, nothing written',
      p_candidate_id, v_status, coalesce(v_lib, '-');
  end if;

  -- only the columns the script sent, so the table's defaults (id, created_at) apply
  select string_agg(quote_ident(k), ', ') into v_cols from jsonb_object_keys(p_row) as k;
  execute format(
    'insert into hadith_library (%1$s) select %1$s from jsonb_populate_record(null::hadith_library, $1) returning id::text',
    v_cols) into v_id using p_row;

  insert into hadith_promotions (candidate_id, library_id, promote_mode, reviewed_by, source_deeplink, columns_written)
  values (p_candidate_id, v_id, 'insert', p_reviewer, p_deeplink, p_columns);

  update hadith_candidates
     set status = 'promoted', promote_mode = 'insert', promoted_library_id = v_id
   where candidate_id = p_candidate_id;

  return v_id;
end
$$;

-- server-side only: the pipeline calls it with the service-role key
revoke all on function public.promote_candidate(uuid, jsonb, text, text, text[]) from public, anon, authenticated;
grant execute on function public.promote_candidate(uuid, jsonb, text, text, text[]) to service_role;

notify pgrst, 'reload schema';

-- Check (read the result): one row, the function exists and anon cannot run it.
select p.proname,
       has_function_privilege('anon', p.oid, 'execute')         as anon_can_execute,
       has_function_privilege('service_role', p.oid, 'execute') as service_role_can_execute
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'promote_candidate';
