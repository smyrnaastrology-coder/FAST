-- Allow users to edit only the text of content they own.
-- Run in Supabase SQL Editor before enabling the app update actions.

drop policy if exists co_update on public.comments;
create policy co_update on public.comments
  for update to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

grant update (text) on public.comments to authenticated;
grant update (caption) on public.posts to authenticated;
