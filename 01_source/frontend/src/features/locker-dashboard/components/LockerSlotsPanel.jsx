// 01_source/frontend/src/features/locker-dashboard/components/LockerSlotsPanel.jsx

import React from "react";
import Carousel from "./Carousel.jsx";
import SlotCard from "./SlotCard.jsx";

export default function LockerSlotsPanel({
  totalSlots,
  activeGroup,
  setActiveGroup,
  groupSlotsList,
  slots,
  selectedSlot,
  onSelectSlot,
  hasActiveSlotSelection,
  slotSelectionRemainingSec,
}) {
  const totalGroups = Math.max(1, Math.ceil(Number(totalSlots || 0) / 4));

  return (
    <section
      style={{
        background: "rgba(255,255,255,0.08)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 16,
        padding: 16,
        display: "grid",
        gap: 16,
      }}
    >
      <div>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Slots / Gavetas</div>
        <div style={{ fontSize: 12, opacity: 0.72 }}>
          Selecione uma gaveta disponível para iniciar o fluxo operacional.
        </div>
      </div>

      {hasActiveSlotSelection ? (
        <div
          style={{
            fontSize: 12,
            borderRadius: 10,
            padding: 10,
            background: "rgba(27,88,131,0.22)",
            border: "1px solid rgba(27,88,131,0.35)",
          }}
        >
          Seleção ativa da gaveta <b>{selectedSlot}</b> • expira em{" "}
          <b>{slotSelectionRemainingSec}s</b>
        </div>
      ) : null}

      <Carousel
        pages={totalGroups}
        activeIndex={activeGroup}
        onPrev={() => setActiveGroup((prev) => Math.max(0, prev - 1))}
        onNext={() => setActiveGroup((prev) => Math.min(totalGroups - 1, prev + 1))}
        onGo={setActiveGroup}
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          gap: 12,
        }}
      >
        {groupSlotsList.map((slot) => {
          const slotData = slots[slot] || { state: "AVAILABLE" };
          const existsInLocker = slot <= totalSlots;

          return (
            <div key={slot} style={{ opacity: existsInLocker ? 1 : 0.3 }}>
              <SlotCard
                slot={slot}
                state={existsInLocker ? slotData.state : "OUT_OF_STOCK"}
                name={existsInLocker ? slotData.name : null}
                skuId={existsInLocker ? slotData.sku_id : null}
                priceCents={existsInLocker ? slotData.price_cents : null}
                isActive={existsInLocker ? slotData.is_active : false}
                hasCatalogData={existsInLocker ? Boolean(slotData.sku_id) : false}
                selected={selectedSlot === slot}
                disabled={!existsInLocker || slotData.state !== "AVAILABLE"}
                onClick={() => onSelectSlot(slot)}
              />
            </div>
          );
        })}
      </div>
    </section>
  );
}