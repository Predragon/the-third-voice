## 🔐 Supabase Setup: Enabling Row Level Security (RLS)

For security and data isolation, it is **CRUCIAL** to enable Row Level Security (RLS) on your Supabase tables. This ensures users can only access their own data.

**Steps:**

1.  Go to your Supabase project dashboard.
2.  Navigate to **Table Editor** or **Authentication > Policies**.
3.  For each of the following tables, enable RLS and create the specified policies:

    * `public.ai_response_cache`
    * `public.contacts`
    * `public.feedback`
    * `public.interpretations`
    * `public.messages`

**SQL Commands for RLS Policies (Run these in your Supabase SQL Editor):**

```sql
-- Enable Row Level Security for tables
ALTER TABLE public.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_response_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interpretations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (users can only access their own data)
-- POLICY: Users can manage their own contacts
CREATE POLICY "Users can manage their own contacts" ON public.contacts
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- POLICY: Users can manage their own messages
CREATE POLICY "Users can manage their own messages" ON public.messages
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- POLICY: Users can manage their own cache
CREATE POLICY "Users can manage their own cache" ON public.ai_response_cache
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- POLICY: Users can manage their own interpretations
CREATE POLICY "Users can manage their own interpretations" ON public.interpretations
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- POLICY: Users can manage their own feedback
CREATE POLICY "Users can manage their own feedback" ON public.feedback
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
