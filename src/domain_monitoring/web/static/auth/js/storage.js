export function createStateManager(storageKey, defaults) {
  function readState() {
    try {
      const raw = window.sessionStorage.getItem(storageKey);
      return raw ? { ...defaults, ...JSON.parse(raw) } : { ...defaults };
    } catch (_error) {
      return { ...defaults };
    }
  }

  function writeState(patch) {
    const next = { ...readState(), ...patch };
    try {
      window.sessionStorage.setItem(storageKey, JSON.stringify(next));
    } catch (_error) {
      // ignore storage errors
    }
    return next;
  }

  return {
    readState,
    writeState,
  };
}