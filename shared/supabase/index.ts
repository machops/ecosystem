/**
 * Supabase integration module
 * Provides database client, types, and utilities for the ecosystem application
 */

export { supabase } from './client';
export { supabaseAdmin } from './server';
export { useAuth, useRealtimeSubscription } from './hooks';
export type { User, AuditLog, Session, NotificationPreferences, Database } from './types';
