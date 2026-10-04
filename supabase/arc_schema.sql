-- ARC cloud schema reference.
-- Applied to Supabase project ixlzqkixximckmhbozsd on 2026-10-04.

create table if not exists public.arc_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default 'ARC User' check (char_length(trim(display_name)) between 1 and 40),
  plan text not null default 'free' check (plan in ('free', 'premium')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.arc_user_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  state jsonb not null default '{}'::jsonb,
  schema_version integer not null default 1 check (schema_version > 0),
  updated_at timestamptz not null default now()
);

alter table public.arc_profiles enable row level security;
alter table public.arc_user_state enable row level security;

grant select, insert, delete on public.arc_profiles to authenticated;
revoke update on public.arc_profiles from authenticated;
grant update (display_name, updated_at) on public.arc_profiles to authenticated;
grant select, insert, update, delete on public.arc_user_state to authenticated;

drop policy if exists "arc_profiles_select_own" on public.arc_profiles;
create policy "arc_profiles_select_own" on public.arc_profiles
for select to authenticated using ((select auth.uid()) = user_id);

drop policy if exists "arc_profiles_insert_own" on public.arc_profiles;
create policy "arc_profiles_insert_own" on public.arc_profiles
for insert to authenticated
with check ((select auth.uid()) = user_id and plan = 'free');

drop policy if exists "arc_profiles_update_own" on public.arc_profiles;
create policy "arc_profiles_update_own" on public.arc_profiles
for update to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

drop policy if exists "arc_profiles_delete_own" on public.arc_profiles;
create policy "arc_profiles_delete_own" on public.arc_profiles
for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists "arc_state_select_own" on public.arc_user_state;
create policy "arc_state_select_own" on public.arc_user_state
for select to authenticated using ((select auth.uid()) = user_id);

drop policy if exists "arc_state_insert_own" on public.arc_user_state;
create policy "arc_state_insert_own" on public.arc_user_state
for insert to authenticated with check ((select auth.uid()) = user_id);

drop policy if exists "arc_state_update_own" on public.arc_user_state;
create policy "arc_state_update_own" on public.arc_user_state
for update to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

drop policy if exists "arc_state_delete_own" on public.arc_user_state;
create policy "arc_state_delete_own" on public.arc_user_state
for delete to authenticated using ((select auth.uid()) = user_id);
