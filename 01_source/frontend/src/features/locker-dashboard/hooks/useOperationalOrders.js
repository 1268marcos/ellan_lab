// 01_source/frontend/src/features/locker-dashboard/hooks/useOperationalOrders.js
/**
 * * Responsável por:
 * fetchAllOperationalOrders
 * fetchOrdersOnce
 * filtros
 * paginação
 * ordersData, ordersLoading, ordersError
 * ordersPage, ordersPageSize, ordersTotal, ordersHasNext, ordersHasPrev
 */

// 01_source/frontend/src/features/locker-dashboard/hooks/useOperationalOrders.js

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchAllOperationalOrders,
  paginateOperationalOrders,
} from "../services/operationalOrdersService.js";

export default function useOperationalOrders({
  orderPickupBase,
  token,
  region,
  selectedLocker,
}) {
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [ordersError, setOrdersError] = useState("");
  const [ordersFilterStatus, setOrdersFilterStatus] = useState("");
  const [ordersFilterChannel, setOrdersFilterChannel] = useState("");
  const [ordersData, setOrdersData] = useState([]);
  const [showOrdersPanel, setShowOrdersPanel] = useState(true);

  const [ordersPage, setOrdersPage] = useState(1);
  const [ordersPageSize, setOrdersPageSize] = useState(10);
  const [ordersTotal, setOrdersTotal] = useState(0);
  const [ordersHasNext, setOrdersHasNext] = useState(false);
  const [ordersHasPrev, setOrdersHasPrev] = useState(false);
  const [ordersTableDensity, setOrdersTableDensity] = useState("10");

  const fetchOrdersOnce = useCallback(
    async (targetPage = ordersPage, targetPageSize = ordersPageSize) => {
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

        setOrdersData(page.pageItems);
        setOrdersTotal(page.total);
        setOrdersHasPrev(page.hasPrev);
        setOrdersHasNext(page.hasNext);
        setOrdersPage(page.resolvedPage);
        setOrdersPageSize(targetPageSize);
      } catch (error) {
        setOrdersError(String(error?.message || error));
        setOrdersData([]);
        setOrdersTotal(0);
        setOrdersHasPrev(false);
        setOrdersHasNext(false);
      } finally {
        setOrdersLoading(false);
      }
    },
    [
      orderPickupBase,
      ordersFilterChannel,
      ordersFilterStatus,
      ordersPage,
      ordersPageSize,
      region,
      selectedLocker,
      token,
    ]
  );

  useEffect(() => {
    fetchOrdersOnce(1, ordersPageSize);
  }, [fetchOrdersOnce, ordersPageSize, region, selectedLocker?.locker_id]);

  useEffect(() => {
    fetchOrdersOnce(1, ordersPageSize);
  }, [fetchOrdersOnce, ordersFilterStatus, ordersFilterChannel, ordersPageSize]);

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
    fetchOrdersOnce,
  };
}