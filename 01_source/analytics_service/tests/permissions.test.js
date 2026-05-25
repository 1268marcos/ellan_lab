import test from 'node:test'
import assert from 'node:assert/strict'
import { hasPermission, permissionMatches } from '../src/lib/permissions.js'

test('permissionMatches wildcards', () => {
  assert.equal(permissionMatches('lockers.*', 'lockers.read'), true)
  assert.equal(permissionMatches('lockers.*', 'lockers'), true)
  assert.equal(permissionMatches('lockers.*', 'orders.read'), false)
  assert.equal(permissionMatches('*', 'anything.here'), true)
})

test('hasPermission resolves list', () => {
  assert.equal(hasPermission(['analytics.*'], 'analytics.read'), true)
  assert.equal(hasPermission(['ops.read'], 'analytics.read'), false)
})
