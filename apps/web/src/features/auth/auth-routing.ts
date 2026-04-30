type AuthRouteState = {
  isSignedIn: boolean;
};

export function resolveLandingRoute(authState: AuthRouteState): string | null {
  return authState.isSignedIn ? "/app" : null;
}

export function resolveAppRoute(authState: AuthRouteState): string | null {
  return authState.isSignedIn ? null : "/";
}

