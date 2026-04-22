// 01_source/frontend/src/features/locker-dashboard/hooks/useLockerRegistry.js
/**
 *  * Responsável por: 
 * - buscar lockers no gateway
 * - aplicar fallback contingencial 
 * - expor lockers, selectedLocker, selectedLockerId, setSelectedLockerId
 * - expor lockersLoading, lockersError, lockersSource
 * 
 * Isso isola a seleção de locker e remove esse bloco da página. Hoje isso 
 * está misturado no componente principal.
 */

// 01_source/frontend/src/features/locker-dashboard/hooks/useLockerRegistry.js

import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchLockersWithFallback } from "../services/lockerRegistryService.js";

export default function useLockerRegistry({
  region,
  gatewayBase,
  orderPickupBase,
  channel = "ONLINE",
  tenant = "",
}) {
  const [lockers, setLockers] = useState([]);
  const [lockersLoading, setLockersLoading] = useState(false);
  const [lockersError, setLockersError] = useState("");
  const [lockersSource, setLockersSource] = useState("loading");
  const [selectedLockerId, setSelectedLockerId] = useState("");

  const selectedLocker = useMemo(
    () => lockers.find((item) => item.locker_id === selectedLockerId) || lockers[0] || null,
    [lockers, selectedLockerId]
  );

  const fetchLockersOnce = useCallback(async () => {
    setLockersLoading(true);
    setLockersError("");

    try {
      const result = await fetchLockersWithFallback({
        gatewayBase,
        region,
        orderPickupBase,
        channel,
        tenant,
      });

      setLockers(result.items || []);
      setLockersSource(result.source || "fallback");
      setLockersError(result.error || "");
    } finally {
      setLockersLoading(false);
    }
  }, [channel, gatewayBase, orderPickupBase, region, tenant]);

  useEffect(() => {
    fetchLockersOnce();
  }, [fetchLockersOnce]);

  useEffect(() => {
    if (!lockers.length) {
      setSelectedLockerId("");
      return;
    }

    setSelectedLockerId((prev) => {
      if (prev && lockers.some((locker) => locker.locker_id === prev)) {
        return prev;
      }
      return lockers[0].locker_id;
    });
  }, [lockers]);

  return {
    lockers,
    lockersLoading,
    lockersError,
    lockersSource,
    selectedLockerId,
    setSelectedLockerId,
    selectedLocker,
    fetchLockersOnce,
  };
}