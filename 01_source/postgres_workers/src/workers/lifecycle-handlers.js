import { randomUUID } from 'crypto'
import { releaseLockerSlot } from '../lib/runtime.js'
import { enqueueUserNotification } from '../lib/notify.js'
import { logger } from '../lib/logger.js'

function norm(v) {
  return v == null ? '' : String(v).trim().toUpperCase()
}

async function orderSnapshot(client, orderId) {
  const { rows } = await client.query(
    `SELECT id, user_id, amount_cents, region, totem_id, status, payment_status, paid_at, picked_up_at, channel
     FROM orders WHERE id = $1 LIMIT 1`,
    [orderId],
  )
  return rows[0] || null
}

async function latestPickup(client, orderId) {
  const { rows } = await client.query(
    `SELECT id, status, lifecycle_stage, locker_id, machine_id, slot
     FROM pickups WHERE order_id = $1 ORDER BY created_at DESC, id DESC LIMIT 1`,
    [orderId],
  )
  return rows[0] || null
}

async function latestAllocation(client, orderId) {
  const { rows } = await client.query(
    `SELECT id, locker_id, slot, state FROM allocations
     WHERE order_id = $1 ORDER BY created_at DESC, id DESC LIMIT 1`,
    [orderId],
  )
  return rows[0] || null
}

export async function handlePrepaymentTimeout(client, deadline) {
  const now = new Date()
  const order = await orderSnapshot(client, deadline.order_id)
  if (!order) {
    await client.query(
      `UPDATE lifecycle_deadlines SET status = 'FAILED', failure_count = failure_count + 1, updated_at = $2 WHERE id = $1`,
      [deadline.id, now],
    )
    return
  }
  const paid =
    order.paid_at != null ||
    order.picked_up_at != null ||
    ['APPROVED', 'PAID', 'CAPTURED', 'SETTLED'].includes(norm(order.payment_status)) ||
    ['PAID_PENDING_PICKUP', 'DISPENSED', 'PICKED_UP', 'COMPLETED', 'FULFILLED'].includes(
      norm(order.status),
    )
  if (paid) {
    await client.query(
      `UPDATE lifecycle_deadlines SET status = 'CANCELLED', cancelled_at = $2, updated_at = $2 WHERE id = $1`,
      [deadline.id, now],
    )
    return
  }
  await client.query(
    `UPDATE orders SET status = 'CANCELLED', updated_at = $2 WHERE id = $1`,
    [deadline.order_id, now],
  )
  const alloc = await latestAllocation(client, deadline.order_id)
  if (alloc) {
    await client.query(
      `UPDATE allocations SET state = 'RELEASED', released_at = COALESCE(released_at, $2), locked_until = NULL WHERE id = $1`,
      [alloc.id, now],
    )
    await releaseLockerSlot({
      regionCode: order.region,
      lockerId: alloc.locker_id || order.totem_id,
      slot: alloc.slot,
      allocationId: alloc.id,
    })
  }
  await enqueueUserNotification(client, {
    userId: order.user_id,
    orderId: order.id,
    templateKey: 'lifecycle.prepayment_timeout',
    dedupeKey: `lifecycle.prepayment_timeout:${order.id}`,
    payload: { deadline_type: 'PREPAYMENT_TIMEOUT', order_id: order.id },
  })
  await client.query(
    `UPDATE lifecycle_deadlines SET status = 'EXECUTED', executed_at = $2, updated_at = $2 WHERE id = $1`,
    [deadline.id, now],
  )
  logger.info('lifecycle_prepayment_timeout_executed', { order_id: order.id, deadline_id: deadline.id })
}

export async function handlePostpaymentExpiry(client, deadline) {
  const now = new Date()
  const order = await orderSnapshot(client, deadline.order_id)
  if (!order) {
    await client.query(
      `UPDATE lifecycle_deadlines SET status = 'FAILED', failure_count = failure_count + 1, updated_at = $2 WHERE id = $1`,
      [deadline.id, now],
    )
    return
  }
  if (order.picked_up_at != null || norm(order.status) === 'PICKED_UP') {
    await client.query(
      `UPDATE lifecycle_deadlines SET status = 'CANCELLED', cancelled_at = $2, updated_at = $2 WHERE id = $1`,
      [deadline.id, now],
    )
    return
  }
  await client.query(
    `UPDATE orders SET status = 'EXPIRED', updated_at = $2 WHERE id = $1`,
    [deadline.order_id, now],
  )
  const pickup = await latestPickup(client, deadline.order_id)
  const alloc = await latestAllocation(client, deadline.order_id)
  if (pickup) {
    await client.query(
      `UPDATE pickups SET status = 'EXPIRED', lifecycle_stage = 'EXPIRED', expired_at = $2 WHERE id = $1`,
      [pickup.id, now],
    )
    await client.query(
      `UPDATE pickup_tokens SET used_at = $2 WHERE pickup_id = $1 AND used_at IS NULL`,
      [pickup.id, now],
    )
  }
  if (alloc) {
    await client.query(
      `UPDATE allocations SET state = 'RELEASED', released_at = COALESCE(released_at, $2), locked_until = NULL WHERE id = $1`,
      [alloc.id, now],
    )
    await releaseLockerSlot({
      regionCode: order.region,
      lockerId: (pickup && (pickup.locker_id || pickup.machine_id)) || alloc.locker_id || order.totem_id,
      slot: pickup?.slot ?? alloc.slot,
      allocationId: alloc.id,
    })
  }
  await enqueueUserNotification(client, {
    userId: order.user_id,
    orderId: order.id,
    templateKey: 'lifecycle.postpayment_expiry',
    dedupeKey: `lifecycle.postpayment_expiry:${order.id}`,
    payload: { deadline_type: 'POSTPAYMENT_EXPIRY', order_id: order.id },
  })
  await client.query(
    `UPDATE lifecycle_deadlines SET status = 'EXECUTED', executed_at = $2, updated_at = $2 WHERE id = $1`,
    [deadline.id, now],
  )
  logger.info('lifecycle_postpayment_expiry_executed', { order_id: order.id, deadline_id: deadline.id })
}

export async function handlePickupTimeout(client, deadline) {
  const now = new Date()
  const order = await orderSnapshot(client, deadline.order_id)
  if (!order) {
    await client.query(
      `UPDATE lifecycle_deadlines SET status = 'FAILED', failure_count = failure_count + 1, updated_at = $2 WHERE id = $1`,
      [deadline.id, now],
    )
    return
  }
  const terminal = [
    'EXPIRED',
    'EXPIRED_CREDIT_50',
    'PICKED_UP',
    'DISPENSED',
    'CANCELLED',
    'REFUNDED',
    'FAILED',
  ]
  if (terminal.includes(norm(order.status))) {
    await client.query(
      `UPDATE lifecycle_deadlines SET status = 'CANCELLED', cancelled_at = $2, updated_at = $2 WHERE id = $1`,
      [deadline.id, now],
    )
    return
  }
  const pickup = await latestPickup(client, deadline.order_id)
  const alloc = await latestAllocation(client, deadline.order_id)
  if (pickup) {
    await client.query(
      `UPDATE pickups SET status = 'EXPIRED', lifecycle_stage = 'EXPIRED', expired_at = $2 WHERE id = $1`,
      [pickup.id, now],
    )
    await client.query(
      `UPDATE pickup_tokens SET used_at = $2 WHERE pickup_id = $1 AND used_at IS NULL`,
      [pickup.id, now],
    )
  }
  if (alloc) {
    await client.query(
      `UPDATE allocations SET state = 'RELEASED', released_at = COALESCE(released_at, $2), locked_until = NULL WHERE id = $1`,
      [alloc.id, now],
    )
  }
  const amount = Number(order.amount_cents || 0)
  let finalStatus = 'EXPIRED'
  if (order.user_id && amount > 0) {
    const creditAmount = Math.max(Math.round(amount * 0.5), 0)
    if (creditAmount > 0) {
      const existing = await client.query(`SELECT id FROM credits WHERE order_id = $1 LIMIT 1`, [
        order.id,
      ])
      if (existing.rowCount === 0) {
        const creditId = randomUUID()
        const expiresAt = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
        await client.query(
          `INSERT INTO credits (
            id, user_id, order_id, amount_cents, status, created_at, updated_at,
            expires_at, source_type, source_reason, notes
          ) VALUES ($1,$2,$3,$4,'AVAILABLE',$5,$5,$6,'PICKUP_EXPIRATION','pickup_not_redeemed','auto 50%')`,
          [creditId, order.user_id, order.id, creditAmount, now, expiresAt],
        )
        finalStatus = 'EXPIRED_CREDIT_50'
      } else {
        finalStatus = 'EXPIRED_CREDIT_50'
      }
    }
  }
  await client.query(`UPDATE orders SET status = $2, updated_at = $3 WHERE id = $1`, [
    order.id,
    finalStatus,
    now,
  ])
  await releaseLockerSlot({
    regionCode: order.region,
    lockerId:
      (pickup && (pickup.locker_id || pickup.machine_id)) ||
      (alloc && alloc.locker_id) ||
      order.totem_id,
    slot: pickup?.slot ?? alloc?.slot,
    allocationId: alloc?.id,
  })
  await enqueueUserNotification(client, {
    userId: order.user_id,
    orderId: order.id,
    templateKey: 'lifecycle.pickup_timeout',
    dedupeKey: `lifecycle.pickup_timeout:${order.id}`,
    payload: { deadline_type: 'PICKUP_TIMEOUT', order_id: order.id, final_status: finalStatus },
  })
  await client.query(
    `UPDATE lifecycle_deadlines SET status = 'EXECUTED', executed_at = $2, updated_at = $2 WHERE id = $1`,
    [deadline.id, now],
  )
  logger.info('lifecycle_pickup_timeout_executed', {
    order_id: order.id,
    deadline_id: deadline.id,
    final_status: finalStatus,
  })
}

export async function executeDeadline(client, deadline) {
  const type = norm(deadline.deadline_type)
  if (type === 'PREPAYMENT_TIMEOUT') return handlePrepaymentTimeout(client, deadline)
  if (type === 'POSTPAYMENT_EXPIRY') return handlePostpaymentExpiry(client, deadline)
  if (type === 'PICKUP_TIMEOUT') return handlePickupTimeout(client, deadline)
  throw new Error(`UNKNOWN_DEADLINE_TYPE:${deadline.deadline_type}`)
}
