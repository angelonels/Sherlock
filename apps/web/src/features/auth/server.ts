export type ServerAuthState = {
  isSignedIn: boolean;
  userId: string | null;
};

export async function getServerAuthState(): Promise<ServerAuthState> {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || !process.env.CLERK_SECRET_KEY) {
    return { isSignedIn: false, userId: null };
  }

  const { auth } = await import("@clerk/nextjs/server");
  const session = await auth();

  return {
    isSignedIn: Boolean(session.userId),
    userId: session.userId,
  };
}

