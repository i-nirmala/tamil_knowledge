-- Code Bloom cloud conversation storage
-- Run this in Supabase Dashboard -> SQL Editor.
-- Supabase Auth owns the users in auth.users.

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  user_email text not null,
  title text not null default 'New conversation',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.messages (
  id bigint generated always as identity primary key,
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  user_email text not null,
  role text not null check (role in ('user','assistant','system')),
  content text not null,
  output_mode text not null default 'Tamil',
  citations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists conversations_user_updated_idx
  on public.conversations(user_id, updated_at desc);

create index if not exists messages_conversation_id_idx
  on public.messages(conversation_id, id);

alter table public.conversations enable row level security;
alter table public.messages enable row level security;

-- These policies are useful if you later expose the tables directly to an authenticated client.
drop policy if exists "Users can view own conversations" on public.conversations;
create policy "Users can view own conversations"
on public.conversations for select to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can insert own conversations" on public.conversations;
create policy "Users can insert own conversations"
on public.conversations for insert to authenticated
with check (auth.uid() = user_id);

drop policy if exists "Users can update own conversations" on public.conversations;
create policy "Users can update own conversations"
on public.conversations for update to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own conversations" on public.conversations;
create policy "Users can delete own conversations"
on public.conversations for delete to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can view own messages" on public.messages;
create policy "Users can view own messages"
on public.messages for select to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can insert own messages" on public.messages;
create policy "Users can insert own messages"
on public.messages for insert to authenticated
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own messages" on public.messages;
create policy "Users can delete own messages"
on public.messages for delete to authenticated
using (auth.uid() = user_id);
