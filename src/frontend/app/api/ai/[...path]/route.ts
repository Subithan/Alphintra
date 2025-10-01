import { NextResponse } from 'next/server'

const disabledPayload = {
  success: false,
  message: 'The AI code assistant is currently disabled pending a security review.',
  details: 'Please contact an administrator if you need access to AI-assisted code features.'
}

function disabledResponse() {
  return NextResponse.json(disabledPayload, {
    status: 503,
    headers: {
      'Cache-Control': 'no-store'
    }
  })
}

export async function POST() {
  return disabledResponse()
}

export async function GET() {
  return disabledResponse()
}

export async function PUT() {
  return disabledResponse()
}

export async function DELETE() {
  return disabledResponse()
}

export async function PATCH() {
  return disabledResponse()
}

export async function OPTIONS() {
  return new Response(null, { status: 204 })
}
