import { AuthenticatedAppShell } from "@/components/app-shell/app-shell";
import { ProtectedAppRoute } from "@/features/auth/protected-app-route";

export const dynamic = "force-dynamic";

export default async function AppPage() {
  return (
    <ProtectedAppRoute>
      <AuthenticatedAppShell />
    </ProtectedAppRoute>
  );
}
