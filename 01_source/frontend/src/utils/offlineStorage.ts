type ChecklistPayload = {
  id?: string
  locker_id: string
  task: string
  status: string
  timestamp?: string
  synced?: boolean
  synced_at?: string | null
}

const DB_NAME = 'EllanLabDB'
const DB_VERSION = 1
const CHECKLIST_STORE = 'checklists'

function openEllanDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(CHECKLIST_STORE)) {
        db.createObjectStore(CHECKLIST_STORE, { keyPath: 'id' })
      }
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('Failed to open offline database.'))
  })
}

function runStore<T>(
  mode: IDBTransactionMode,
  operation: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  return openEllanDb().then((db) => new Promise<T>((resolve, reject) => {
    const tx = db.transaction(CHECKLIST_STORE, mode)
    const store = tx.objectStore(CHECKLIST_STORE)
    const request = operation(store)

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('Offline storage operation failed.'))
    tx.oncomplete = () => db.close()
    tx.onerror = () => {
      db.close()
      reject(tx.error ?? new Error('Offline storage transaction failed.'))
    }
  }))
}

function withOfflineId(checklist: ChecklistPayload): ChecklistPayload {
  return {
    ...checklist,
    id: checklist.id ?? `field-${Date.now()}-${crypto.randomUUID()}`,
    timestamp: checklist.timestamp ?? new Date().toISOString(),
    synced: checklist.synced ?? false,
    synced_at: checklist.synced_at ?? null,
  }
}

export async function saveChecklistOffline(checklist: ChecklistPayload): Promise<ChecklistPayload> {
  const item = withOfflineId(checklist)
  await runStore('readwrite', (store) => store.put(item))
  return item
}

export async function getOfflineChecklists(): Promise<ChecklistPayload[]> {
  return runStore('readonly', (store) => store.getAll())
}

export async function getPendingChecklistCount(): Promise<number> {
  const items = await getOfflineChecklists()
  return items.filter((item) => !item.synced).length
}

export async function syncOfflineChecklists(baseUrl = ''): Promise<{ synced: number; failed: number }> {
  const pending = (await getOfflineChecklists()).filter((item) => !item.synced)
  let synced = 0
  let failed = 0

  for (const item of pending) {
    const response = await fetch(`${baseUrl}/api/v1/field/checklist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        locker_id: item.locker_id,
        task: item.task,
        status: item.status,
        timestamp: item.timestamp,
      }),
    })

    if (!response.ok) {
      failed += 1
      continue
    }

    await runStore('readwrite', (store) => store.put({
      ...item,
      synced: true,
      synced_at: new Date().toISOString(),
    }))
    synced += 1
  }

  return { synced, failed }
}
