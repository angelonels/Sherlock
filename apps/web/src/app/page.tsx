import { LandingPage } from "@/components/landing/landing-page";
import { resolveLandingRoute } from "@/features/auth/auth-routing";
import { getServerAuthState } from "@/features/auth/server";
import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function Home() {
  const authState = await getServerAuthState();
  const destination = resolveLandingRoute(authState);

  if (destination) {
    redirect(destination);
  }

  return <LandingPage />;
}
