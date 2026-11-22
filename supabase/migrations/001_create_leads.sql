-- Run this migration in the Supabase SQL Editor for your SalesPilot project.
create table if not exists public.leads (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    company text not null,
    role text not null default '',
    source text not null default 'Other',
    email text not null default '',
    need text not null,
    notes text not null default '',
    status text not null default 'New'
        check (status in ('New', 'Contacted', 'Qualified', 'Follow-up', 'Won', 'Lost')),
    last_touch text not null default 'Just added',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists leads_user_created_idx
    on public.leads (user_id, created_at);

alter table public.leads enable row level security;

drop policy if exists "Users can read their own leads" on public.leads;
create policy "Users can read their own leads"
    on public.leads for select to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists "Users can create their own leads" on public.leads;
create policy "Users can create their own leads"
    on public.leads for insert to authenticated
    with check ((select auth.uid()) = user_id);

drop policy if exists "Users can update their own leads" on public.leads;
create policy "Users can update their own leads"
    on public.leads for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

drop policy if exists "Users can delete their own leads" on public.leads;
create policy "Users can delete their own leads"
    on public.leads for delete to authenticated
    using ((select auth.uid()) = user_id);

grant select, insert, update, delete on public.leads to authenticated;
