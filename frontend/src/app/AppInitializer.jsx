import { useEffect, useState } from "react";

import useAuthStore from "../stores/authStore";
import LoadingScreen from "./LoadingScreen";

function AppInitializer({ children }) {
  const [initialized, setInitialized] = useState(false);

  const fetchCurrentUser = useAuthStore(
    (state) => state.fetchCurrentUser
  );

  useEffect(() => {
    let active = true;

    const initialize = async () => {
      try {
        await fetchCurrentUser();
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
  }, [fetchCurrentUser]);

  if (!initialized) {
    return <LoadingScreen />;
  }

  return children;
}

export default AppInitializer;
