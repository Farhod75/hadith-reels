import { NextRequest, NextResponse } from 'next/server'
export async function POST(req: NextRequest) {
  return NextResponse.json({ story_behind: '', moral_lesson: '', hook_line: '', key_words: [] })
}
