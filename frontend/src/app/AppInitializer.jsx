import { useEffect, useState } from "react";

import useAuthStore from "../stores/authStore";
import LoadingScreen from "./LoadingScreen";

function AppInitializer({ children }) {
  const [initialized, setInitialized] = useState(false);

  const startDemoSession = useAuthStore(
    (state) => state.startDemoSession
  );

  useEffect(() => {
    let active = true;

    const initialize = async () => {
      try {
        await startDemoSession();
      } finally {
        if (active) {
          setInitialized(true);
        }
      }
    };

    initialize();

    return () => {
      active = false;
    };
  }, [startDemoSession]);

  if (!initialized) {
    return <LoadingScreen />;
  }

  return children;
}

export default AppInitializer;
