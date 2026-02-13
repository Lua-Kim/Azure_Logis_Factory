import { useEffect } from "react";

const usePolling = (callback, intervalMs) => {
  useEffect(() => {
    if (!intervalMs) {
      return undefined;
    }
    const timer = setInterval(() => {
      callback();
    }, intervalMs);

    return () => clearInterval(timer);
  }, [callback, intervalMs]);
};

export default usePolling;
