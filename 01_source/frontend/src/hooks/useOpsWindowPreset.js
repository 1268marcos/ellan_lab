import { useCallback, useEffect, useMemo, useState } from "react";

function clamp(value, min, max, fallback) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  return Math.max(min, Math.min(max, numeric));
}

export default function useOpsWindowPreset({
  storageKey,
  defaultValue,
  minValue,
  maxValue,
  presetValues = [],
}) {
  const [windowValue, setWindowValue] = useState(() => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw == null || raw === "") return clamp(defaultValue, minValue, maxValue, defaultValue);
      return clamp(raw, minValue, maxValue, defaultValue);
    } catch (_) {
      return clamp(defaultValue, minValue, maxValue, defaultValue);
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, String(windowValue));
    } catch (_) {
      // fallback silencioso para ambientes sem localStorage
    }
  }, [storageKey, windowValue]);

  const setWindowValueSafe = useCallback(
    (nextValue) => {
      setWindowValue(clamp(nextValue, minValue, maxValue, defaultValue));
    },
    [defaultValue, maxValue, minValue]
  );

  const applyPreset = useCallback(
    (presetValue) => {
      setWindowValueSafe(presetValue);
    },
    [setWindowValueSafe]
  );

  const normalizedPresets = useMemo(() => {
    const unique = Array.from(new Set((presetValues || []).map((item) => clamp(item, minValue, maxValue, defaultValue))));
    return unique.sort((a, b) => a - b);
  }, [defaultValue, maxValue, minValue, presetValues]);

  return {
    windowValue,
    setWindowValue: setWindowValueSafe,
    applyPreset,
    presetValues: normalizedPresets,
  };
}
