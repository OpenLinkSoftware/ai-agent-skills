#!/usr/bin/env node
// YouID minimal Nostr relay client (NIP-01) — no dependencies (Node >= 22 global WebSocket).
// It only moves JSON; signing and signature verification happen in nostr_crypto.py.
//
//   node nostr_relay.mjs query   <wss://relay/> <pubkey-hex> [kinds=0,3,10002]  -> JSON array of events
//   node nostr_relay.mjs publish <wss://relay/> <signed-event.json>             -> relay OK response
import fs from 'fs'

const [, , cmd, relay, arg, kindsArg] = process.argv
const TIMEOUT_MS = 10000

if (typeof WebSocket === 'undefined') {
  console.error('Node >= 22 required (global WebSocket)')
  process.exit(2)
}
if (!cmd || !relay || !arg || !relay.startsWith('wss://')) {
  console.error('usage: nostr_relay.mjs query|publish <wss://relay/> <pubkey-hex|event.json> [kinds]')
  process.exit(2)
}

const ws = new WebSocket(relay)
const timer = setTimeout(() => { console.error(`timeout after ${TIMEOUT_MS} ms`); process.exit(3) }, TIMEOUT_MS)
const done = (code, out) => { clearTimeout(timer); if (out !== undefined) console.log(out); ws.close(); process.exit(code) }

ws.addEventListener('error', (e) => { console.error(`websocket error: ${e.message || e.type}`); process.exit(4) })

if (cmd === 'query') {
  const kinds = (kindsArg || '0,3,10002').split(',').map(Number)
  const sub = 'youid-' + Math.random().toString(36).slice(2, 10)
  const events = []
  ws.addEventListener('open', () => ws.send(JSON.stringify(['REQ', sub, { authors: [arg], kinds }])))
  ws.addEventListener('message', (m) => {
    const msg = JSON.parse(m.data)
    if (msg[0] === 'EVENT' && msg[1] === sub) events.push(msg[2])
    else if (msg[0] === 'EOSE' && msg[1] === sub) {
      ws.send(JSON.stringify(['CLOSE', sub]))
      done(0, JSON.stringify(events, null, 2))
    } else if (msg[0] === 'CLOSED' || msg[0] === 'NOTICE') console.error(`relay ${msg[0]}: ${msg.slice(1).join(' ')}`)
  })
} else if (cmd === 'publish') {
  const ev = JSON.parse(fs.readFileSync(arg, 'utf8'))
  ws.addEventListener('open', () => ws.send(JSON.stringify(['EVENT', ev])))
  ws.addEventListener('message', (m) => {
    const msg = JSON.parse(m.data)
    if (msg[0] === 'OK' && msg[1] === ev.id) done(msg[2] ? 0 : 1, JSON.stringify(msg))
    else if (msg[0] === 'NOTICE') console.error(`relay NOTICE: ${msg[1]}`)
  })
} else {
  console.error(`unknown command ${cmd}`)
  process.exit(2)
}
