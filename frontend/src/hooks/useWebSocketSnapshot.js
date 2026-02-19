import { useEffect, useMemo, useState, useRef } from "react";
import { API_BASE_URL } from "../services/apiClient.js";

const buildWsUrl = (params = {}) => {
  const envUrl = import.meta.env.VITE_WS_URL;
  if (envUrl) return envUrl;
  
  const url = new URL(API_BASE_URL.replace(/^http/, "ws") + "/ws/live");
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
};

const useWebSocketSnapshot = (enabled = true, params = {}) => {
  const [snapshot, setSnapshot] = useState(null);
  const [status, setStatus] = useState("idle");
  
  // useRef를 사용하여 타이머와 소켓 인스턴스를 관리 (리렌더링 시 초기화 방지)
  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  const url = useMemo(
    () => buildWsUrl(params),
    [params.center_id, params.line_id, params.window]
  );

  useEffect(() => {
    if (!enabled) {
      setStatus("disabled");
      return undefined;
    }

    const connect = () => {
      // 기존 연결이 있다면 명시적으로 닫기
      if (socketRef.current) {
        socketRef.current.close();
      }

      setStatus("connecting");
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        setStatus("open");
        console.log("WebSocket connected:", url);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setSnapshot(payload);
        } catch (e) {
          console.error("Malformed payload", e);
        }
      };

      socket.onclose = (event) => {
        setStatus("closed");
        socketRef.current = null;
        // 의도적인 종료가 아닐 때만 3초 후 재연결
        if (!event.wasClean) {
          reconnectTimerRef.current = setTimeout(connect, 3000);
        }
      };

      socket.onerror = () => {
        setStatus("error");
        socket.close();
      };
    };

    connect();

    // [중요] Cleanup 함수: 컴포넌트가 언마운트되거나 URL이 바뀔 때 실행
    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (socketRef.current) {
        // 더 이상 재연결을 시도하지 않도록 onclose를 null로 설정 후 닫기
        socketRef.current.onclose = null;
        socketRef.current.close();
        console.log("WebSocket cleanup: connection closed");
      }
    };
  }, [enabled, url]); // URL이 바뀔 때만 새롭게 연결

  return { snapshot, status };
};

export default useWebSocketSnapshot;