-- Seed data for Supabase local development
-- This file provides test data for development and testing

-- Insert test users (development only)
INSERT INTO public.users (open_id, name, email, login_method, role) VALUES
  ('dev_user_001', 'Developer User', 'dev@example.com', 'oauth', 'user'),
  ('dev_admin_001', 'Admin User', 'admin@example.com', 'oauth', 'admin')
ON CONFLICT (open_id) DO NOTHING;

-- Insert notification preferences for test users
INSERT INTO public.notification_preferences (user_id, email_enabled, push_enabled, sms_enabled)
SELECT id, true, true, false FROM public.users
WHERE open_id IN ('dev_user_001', 'dev_admin_001')
ON CONFLICT (user_id) DO NOTHING;
