import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../services/apiClient.js";

const buildWsUrl = (params = {}) => {
  const envUrl = import.meta.env.VITE_WS_URL;
  if (envUrl) {
    return envUrl;
  }
  const url = new URL(API_BASE_URL.replace(/^http/, "ws") + "/ws/live");
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    url.searchParams.set(key, String(value));
  });
  return url.toString();
};

const useWebSocketSnapshot = (enabled = true, params = {}) => {
  const [snapshot, setSnapshot] = useState(null);
  const [status, setStatus] = useState("idle");
  const url = useMemo(
    () => buildWsUrl(params),
    [params.center_id, params.line_id, params.window]
  );

  useEffect(() => {
    if (!enabled) {
      setStatus("disabled");
      return undefined;
    }

    let socket;
    let reconnectTimer;

    const connect = () => {
      setStatus("connecting");
      socket = new WebSocket(url);

      socket.onopen = () => setStatus("open");
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setSnapshot(payload);
        } catch {
          // Ignore malformed payloads.
        }
      };

      socket.onclose = () => {
        setStatus("closed");
        reconnectTimer = setTimeout(connect, 3000);
      };

      socket.onerror = () => {
        setStatus("error");
        socket.close();
      };
    };

    connect();

    return () => {
      if (socket) {
        socket.close();
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
    };
  }, [enabled, url]);

  return { snapshot, status };
};

export default useWebSocketSnapshot;
