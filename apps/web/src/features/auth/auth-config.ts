export function isAuthBypassEnabled(): boolean {
  return process.env.NEXT_PUBLIC_AUTH_BYPASS === "true";
}

export function isClerkConfigured(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
}
