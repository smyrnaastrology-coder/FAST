-- Hikaye begeni ve yanit tablolari
create table if not exists public.story_likes (
  story_id uuid not null references public.stories(id) on delete cascade,
  user_id  uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (story_id, user_id)
);

create table if not exists public.story_replies (
  id uuid primary key default gen_random_uuid(),
  story_id uuid not null references public.stories(id) on delete cascade,
  sender_id uuid not null references auth.users(id) on delete cascade,
  owner_id  uuid not null references auth.users(id) on delete cascade,
  text text not null,
  created_at timestamptz not null default now()
);

alter table public.story_likes enable row level security;
alter table public.story_replies enable row level security;

create policy "story_likes read" on public.story_likes for select using (true);
create policy "story_likes insert" on public.story_likes for insert with check (auth.uid() = user_id);
create policy "story_likes delete" on public.story_likes for delete using (auth.uid() = user_id);

create policy "story_replies read owner" on public.story_replies for select using (auth.uid() = owner_id or auth.uid() = sender_id);
create policy "story_replies insert" on public.story_replies for insert with check (auth.uid() = sender_id);
