
import { type NextRequest, NextResponse } from 'next/server'
import { updateSession } from '@/utils/supabase/middleware'
import { createServerClient } from '@supabase/ssr'

export async function middleware(request: NextRequest) {
    // Update session first
    const response = await updateSession(request)

    // Create client to check auth status
    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                get(name: string) {
                    return request.cookies.get(name)?.value
                },
            },
        }
    )

    let session = null;
    try {
        const { data } = await supabase.auth.getSession()
        session = data.session;
    } catch (e: any) {
        console.error("Supabase Middleware Fetch Error:", e)
        if (e.cause) {
            console.error("Underlying cause:", e.cause)
        } else if (e.message) {
            console.error("Error message:", e.message)
        }
    }

    try {
        // Protect /dashboard route
        if (request.nextUrl.pathname.startsWith('/dashboard') && !session) {
            return NextResponse.redirect(new URL('/login', request.url))
        }

        // Redirect logged-in users away from auth pages
        if ((request.nextUrl.pathname.startsWith('/login') || request.nextUrl.pathname.startsWith('/signup')) && session) {
            return NextResponse.redirect(new URL('/dashboard', request.url))
        }
    } catch (error: any) {
        console.error("Middleware Auth Check Error:", error.message)
    }

    return response
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         * Feel free to modify this pattern to include more paths.
         */
        '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
    ],
}
