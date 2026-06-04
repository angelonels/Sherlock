const isVercelBuild = Boolean(process.env.VERCEL_ENV);

if (!isVercelBuild) {
  process.exit(0);
}

const errors = [];
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const clerkPublishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";

if (process.env.NEXT_PUBLIC_AUTH_BYPASS === "true") {
  errors.push("NEXT_PUBLIC_AUTH_BYPASS must not be enabled on Vercel.");
}
if (!clerkPublishableKey) {
  errors.push("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is required on Vercel.");
}
if (!apiBaseUrl) {
  errors.push("NEXT_PUBLIC_API_BASE_URL is required on Vercel.");
} else if (/^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(?::|\/|$)/i.test(apiBaseUrl)) {
  errors.push("NEXT_PUBLIC_API_BASE_URL must reference the public production API on Vercel.");
} else if (!apiBaseUrl.startsWith("https://")) {
  errors.push("NEXT_PUBLIC_API_BASE_URL must use HTTPS on Vercel.");
}

if (errors.length > 0) {
  console.error(`Invalid Vercel deployment configuration:\n- ${errors.join("\n- ")}`);
  process.exit(1);
}
