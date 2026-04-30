import { resolveAppRoute } from "@/features/auth/auth-routing";
import { getServerAuthState } from "@/features/auth/server";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

type ProtectedAppRouteProps = {
  children: ReactNode;
};

export async function ProtectedAppRoute({ children }: ProtectedAppRouteProps) {
  const authState = await getServerAuthState();
  const destination = resolveAppRoute(authState);

  if (destination) {
    redirect(destination);
  }

  return <>{children}</>;
}

