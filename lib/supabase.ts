import { createClient } from '@supabase/supabase-js'

const sbUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const sbAnon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const sbService = process.env.SUPABASE_SERVICE_ROLE_KEY!

// Client-side (public)
export const supabase = createClient(sbUrl, sbAnon)

// Server-side only — bypasses RLS
export const supabaseAdmin = createClient(sbUrl, sbService)