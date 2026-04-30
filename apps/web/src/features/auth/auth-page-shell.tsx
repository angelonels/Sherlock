import { AuthPanel } from "@/features/auth/auth-panel";
import Link from "next/link";

type AuthPageShellProps = {
  mode: "sign-in" | "sign-up";
};

export function AuthPageShell({ mode }: AuthPageShellProps) {
  return (
    <main className="grid min-h-dvh place-items-center bg-[#f7f3ec] px-4 py-12 text-[#241f1a]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_14%_8%,rgba(201,129,70,0.12),transparent_28rem),radial-gradient(circle_at_88%_18%,rgba(95,106,82,0.11),transparent_30rem)]" />
      <div className="relative flex w-full max-w-5xl flex-col items-center gap-8">
        <Link
          href="/"
          className="inline-flex items-center gap-3 text-lg font-semibold tracking-[-0.03em] text-[#241f1a] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-[#b56b32]/25"
        >
          <span className="grid size-9 place-items-center border border-[#241f1a] bg-[#241f1a] text-[#fffaf7] shadow-[3px_3px_0_#d2c3b3]">
            <span className="h-4 w-4 rounded-full border border-[#c98146]" />
          </span>
          Sherlock
        </Link>
        <AuthPanel mode={mode} />
      </div>
    </main>
  );
}

