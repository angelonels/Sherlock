import { AuthenticatedAppShell } from "@/components/app-shell/app-shell";
import { ProtectedAppRoute } from "@/features/auth/protected-app-route";

type ChatPageProps = {
  params: Promise<{
    chatId: string;
  }>;
};

export const dynamic = "force-dynamic";

export default async function ChatPage({ params }: ChatPageProps) {
  const { chatId } = await params;

  return (
    <ProtectedAppRoute>
      <AuthenticatedAppShell activeView="chat" chatId={chatId} />
    </ProtectedAppRoute>
  );
}
