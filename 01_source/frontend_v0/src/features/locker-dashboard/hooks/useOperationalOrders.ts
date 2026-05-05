
/**
 * Responsável por: fetchOrdersOnce, filtros, paginação, ordersData / loading / error
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { NormalizedLockerItem } from "../utils/dashboardMappers";
import { useCheckoutStore } from "../../../store/useCheckoutStore";
import {
  fetchAllOperationalOrders,
  paginateOperationalOrders,
} from "../services/operationalOrdersService";

export type UseOperationalOrdersParams = {
  orderPickupBase: string;
  token: string;
  region: string;
  selectedLocker: NormalizedLockerItem | null;
};

export default function useOperationalOrders({
  orderPickupBase,
  token,
  region,
  selectedLocker,
}: UseOperationalOrdersParams) {
  const ordersLoading = useCheckoutStore((state) => state.ordersLoading);
  const setOrdersLoading = useCheckoutStore((state) => state.setOrdersLoading);
  const ordersError = useCheckoutStore((state) => state.ordersError);
  const setOrdersError = useCheckoutStore((state) => state.setOrdersError);
  const ordersData = useCheckoutStore((state) => state.ordersData);
  const setOrdersData = useCheckoutStore((state) => state.setOrdersData);
  const [ordersFilterStatus, setOrdersFilterStatus] = useState("");
  const [ordersFilterChannel, setOrdersFilterChannel] = useState("");
  const [showOrdersPanel, setShowOrdersPanel] = useState(true);

  const [ordersPage, setOrdersPage] = useState(1);
  const [ordersPageSize, setOrdersPageSize] = useState(10);
  const [ordersTotal, setOrdersTotal] = useState(0);
  const [ordersHasNext, setOrdersHasNext] = useState(false);
  const [ordersHasPrev, setOrdersHasPrev] = useState(false);
  const [ordersTableDensity, setOrdersTableDensity] = useState("10");
  const [ordersLastUpdatedAt, setOrdersLastUpdatedAt] = useState<number | null>(null);
  const requestSeqRef = useRef(0);

  const fetchOrdersOnce = useCallback(
    async (targetPage = 1, targetPageSize = ordersPageSize) => {
      const requestSeq = requestSeqRef.current + 1;
      requestSeqRef.current = requestSeq;
      setOrdersLoading(true);
      setOrdersError("");

      try {
        const allItems = await fetchAllOperationalOrders({
          orderPickupBase,
          token,
          region,
          status: ordersFilterStatus || undefined,
          channel: ordersFilterChannel || undefined,
        });

        const filteredItems = selectedLocker?.locker_id
          ? allItems.filter(
              (item) => (item?.locker_id || item?.totem_id) === selectedLocker.locker_id
            )
          : allItems;

        const page = paginateOperationalOrders({
          items: filteredItems,
          page: targetPage,
          pageSize: targetPageSize,
        });

        if (requestSeq !== requestSeqRef.current) return;

        setOrdersData(page.pageItems);
        setOrdersTotal(page.total);
        setOrdersHasPrev(page.hasPrev);
        setOrdersHasNext(page.hasNext);
        setOrdersPage(page.resolvedPage);
        setOrdersPageSize(targetPageSize);
        setOrdersLastUpdatedAt(Date.now());
      } catch (error: unknown) {
        if (requestSeq !== requestSeqRef.current) return;
        setOrdersError(String(error instanceof Error ? error.message : error));
        setOrdersData([]);
        setOrdersTotal(0);
        setOrdersHasPrev(false);
        setOrdersHasNext(false);
      } finally {
        if (requestSeq !== requestSeqRef.current) return;
        setOrdersLoading(false);
      }
    },
    [
      orderPickupBase,
      ordersFilterChannel,
      ordersFilterStatus,
      ordersPageSize,
      region,
      selectedLocker?.locker_id,
      token,
    ]
  );

  useEffect(() => {
    setOrdersPage(1);
  }, [region, selectedLocker?.locker_id, ordersFilterStatus, ordersFilterChannel, ordersPageSize]);

  useEffect(() => {
    fetchOrdersOnce(ordersPage, ordersPageSize);
  }, [fetchOrdersOnce, ordersPage, ordersPageSize]);

  const totalOrdersPages = useMemo(
    () => Math.max(1, Math.ceil(ordersTotal / ordersPageSize)),
    [ordersPageSize, ordersTotal]
  );

  const visibleOrdersFrom = useMemo(
    () => (ordersTotal === 0 ? 0 : (ordersPage - 1) * ordersPageSize + 1),
    [ordersPage, ordersPageSize, ordersTotal]
  );

  const visibleOrdersTo = useMemo(
    () => Math.min(ordersPage * ordersPageSize, ordersTotal),
    [ordersPage, ordersPageSize, ordersTotal]
  );

  const ordersTableHeight = useMemo(
    () => (ordersTableDensity === "3" ? 3 * 44 + 44 : 10 * 44 + 44),
    [ordersTableDensity]
  );

  return {
    ordersLoading,
    ordersError,
    ordersFilterStatus,
    setOrdersFilterStatus,
    ordersFilterChannel,
    setOrdersFilterChannel,
    ordersData,
    setOrdersData,
    showOrdersPanel,
    setShowOrdersPanel,
    ordersPage,
    setOrdersPage,
    ordersPageSize,
    setOrdersPageSize,
    ordersTotal,
    ordersHasNext,
    ordersHasPrev,
    ordersTableDensity,
    setOrdersTableDensity,
    totalOrdersPages,
    visibleOrdersFrom,
    visibleOrdersTo,
    ordersTableHeight,
    ordersLastUpdatedAt,
    fetchOrdersOnce,
  };
}
