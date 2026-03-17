import { useCallback, useEffect, useMemo } from "react";
import { getTelegramWebApp, type WebApp, type TelegramUser } from "../utils/telegram";

interface UseTelegramReturn {
  webApp: WebApp | null;
  user: TelegramUser | null;
  initData: string;
  colorScheme: "light" | "dark";
  themeParams: WebApp["themeParams"];
  showMainButton: (text: string, onClick: () => void) => void;
  hideMainButton: () => void;
  showBackButton: (onClick: () => void) => void;
  hideBackButton: () => void;
}

export function useTelegram(): UseTelegramReturn {
  const webApp = useMemo(() => getTelegramWebApp(), []);

  useEffect(() => {
    webApp?.ready();
    webApp?.expand();
  }, [webApp]);

  const showMainButton = useCallback(
    (text: string, onClick: () => void) => {
      if (!webApp) return;
      webApp.MainButton.setText(text);
      webApp.MainButton.onClick(onClick);
      webApp.MainButton.show();
    },
    [webApp]
  );

  const hideMainButton = useCallback(() => {
    webApp?.MainButton.hide();
  }, [webApp]);

  const showBackButton = useCallback(
    (onClick: () => void) => {
      if (!webApp) return;
      webApp.BackButton.onClick(onClick);
      webApp.BackButton.show();
    },
    [webApp]
  );

  const hideBackButton = useCallback(() => {
    webApp?.BackButton.hide();
  }, [webApp]);

  return {
    webApp,
    user: webApp?.initDataUnsafe?.user ?? null,
    initData: webApp?.initData ?? "",
    colorScheme: webApp?.colorScheme ?? "light",
    themeParams: webApp?.themeParams ?? {},
    showMainButton,
    hideMainButton,
    showBackButton,
    hideBackButton,
  };
}
