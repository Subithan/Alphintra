'use client'

import React, { useEffect, useState } from 'react'
import GradientBorder from '../../GradientBorder'

type OrderBookEntry = {
  price: number
  quantity: number
}

type OrderBookTableProps = {
  data: OrderBookEntry[]
  side: 'buy' | 'sell'
  maxTotal: number
  range: number
}

const OrderBookTable: React.FC<OrderBookTableProps> = ({ data, side, range }) => {
  // Show only first 10 entries
  const visibleData = data.slice(0, 20)

  return (
    <div className="max-h-[300px] overflow-y-auto">
      <table className="w-full text-sm">
        <tbody>
          {visibleData.map((order, index) => {
            const total = order.price * order.quantity
            const roundedPrice =
              range === 0.1
                ? Math.floor(order.price * 10) / 10
                : range === 1
                ? Math.floor(order.price)
                : Math.round(order.price / 10) * 10

            return (
              <tr key={index} className={side === 'buy' ? 'text-[#0b9981]' : 'text-red-500'}>
                <td>{roundedPrice.toLocaleString()}</td>
                <td>{order.quantity.toFixed(4)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

const OrderBook: React.FC = () => {
  const [bids, setBids] = useState<OrderBookEntry[]>([])
  const [asks, setAsks] = useState<OrderBookEntry[]>([])
  const [range, setRange] = useState<number>(1)

  useEffect(() => {
    const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms')

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      const format = (entries: string[][]): OrderBookEntry[] =>
        entries.map(([price, quantity]) => ({
          price: parseFloat(price),
          quantity: parseFloat(quantity),
        }))

      setBids(format(data.bids))
      setAsks(format(data.asks))
    }

    return () => ws.close()
  }, [])

  const maxBidTotal = Math.max(...bids.map((b) => b.price * b.quantity), 1)
  const maxAskTotal = Math.max(...asks.map((a) => a.price * a.quantity), 1)

  return (
    <GradientBorder gradientAngle="45deg" className="p-5">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">Order Book</h2>
        <select
          value={range}
          onChange={(e) => setRange(Number(e.target.value))}
          className="border rounded px-2 py-1 bg-white dark:bg-gray-800 text-black dark:text-white"
        >
          <option value={0.1}>0.1</option>
          <option value={1}>1</option>
          <option value={10}>10</option>
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <div>
          <h3 className="text-sm font-semibold mb-1">Asks (Sell)</h3>
          <OrderBookTable data={asks} side="sell" maxTotal={maxAskTotal} range={range} />
        </div>
        <div>
          <h3 className="text-sm font-semibold mb-1">Bids (Buy)</h3>
          <OrderBookTable data={bids} side="buy" maxTotal={maxBidTotal} range={range} />
        </div>
      </div>
    </GradientBorder>
  )
}

export default OrderBook
