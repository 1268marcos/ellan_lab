import { useCallback, useEffect, useMemo, useState } from "react";

function clamp(value: unknown, min: number, max: number, fallback: number): number {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  return Math.max(min, Math.min(max, numeric));
}

export type UseOpsWindowPresetParams = {
  storageKey: string;
  defaultValue: number;
  minValue: number;
  maxValue: number;
  presetValues?: number[];
};

export type UseOpsWindowPresetResult = {
  windowValue: number;
  setWindowValue: (nextValue: number | string) => void;
  applyPreset: (presetValue: number) => void;
  presetValues: number[];
};

export default function useOpsWindowPreset({
  storageKey,
  defaultValue,
  minValue,
  maxValue,
  presetValues = [],
}: UseOpsWindowPresetParams): UseOpsWindowPresetResult {
  const [windowValue, setWindowValue] = useState(() => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw == null || raw === "") return clamp(defaultValue, minValue, maxValue, defaultValue);
      return clamp(raw, minValue, maxValue, defaultValue);
    } catch {
      return clamp(defaultValue, minValue, maxValue, defaultValue);
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, String(windowValue));
    } catch {
      // fallback silencioso para ambientes sem localStorage
    }
  }, [storageKey, windowValue]);

  const setWindowValueSafe = useCallback(
    (nextValue: number | string) => {
      setWindowValue(clamp(nextValue, minValue, maxValue, defaultValue));
    },
    [defaultValue, maxValue, minValue]
  );

  const applyPreset = useCallback(
    (presetValue: number) => {
      setWindowValueSafe(presetValue);
    },
    [setWindowValueSafe]
  );

  const normalizedPresets = useMemo(() => {
    const unique = Array.from(
      new Set((presetValues || []).map((item) => clamp(item, minValue, maxValue, defaultValue)))
    );
    return unique.sort((a, b) => a - b);
  }, [defaultValue, maxValue, minValue, presetValues]);

  return {
    windowValue,
    setWindowValue: setWindowValueSafe,
    applyPreset,
    presetValues: normalizedPresets,
  };
}
