import type { ReactNode } from "react";
import { RequireAuth } from "./auth-gate";

type ProtectedAppRouteProps = {
  children: ReactNode;
};

export function ProtectedAppRoute({ children }: ProtectedAppRouteProps) {
  return <RequireAuth>{children}</RequireAuth>;
}
