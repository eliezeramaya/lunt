import { PreviewResponse } from '@/lib/api'
import { useDraft } from '@/store/useDraft'

interface PriceBreakdownTableProps {
  preview: PreviewResponse
}

export default function PriceBreakdownTable({ preview }: PriceBreakdownTableProps) {
  const { adjustments, setAdjustment } = useDraft()

  const handlePriceChange = (codigoInsumo: string, value: string) => {
    const precio = parseFloat(value)
    if (!isNaN(precio)) {
      setAdjustment(codigoInsumo, precio)
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border border-gray-300 px-4 py-2 text-left">Código</th>
            <th className="border border-gray-300 px-4 py-2 text-left">Descripción</th>
            <th className="border border-gray-300 px-4 py-2 text-left">Unidad</th>
            <th className="border border-gray-300 px-4 py-2 text-right">Cantidad</th>
            <th className="border border-gray-300 px-4 py-2 text-right">Precio Unitario</th>
            <th className="border border-gray-300 px-4 py-2 text-right">Subtotal</th>
          </tr>
        </thead>
        <tbody>
          {preview.breakdown.map((item) => {
            const adjustedPrice = adjustments[item.codigo_insumo]
            const displayPrice = adjustedPrice ?? item.precio_unitario
            const subtotal = item.cantidad * displayPrice

            return (
              <tr key={item.codigo_insumo} className="hover:bg-gray-50">
                <td className="border border-gray-300 px-4 py-2">{item.codigo_insumo}</td>
                <td className="border border-gray-300 px-4 py-2">{item.descripcion}</td>
                <td className="border border-gray-300 px-4 py-2">{item.unidad}</td>
                <td className="border border-gray-300 px-4 py-2 text-right">
                  {item.cantidad.toFixed(4)}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  <input
                    type="number"
                    step="0.01"
                    className="w-full text-right border border-gray-300 rounded px-2 py-1"
                    value={displayPrice.toFixed(2)}
                    onChange={(e) => handlePriceChange(item.codigo_insumo, e.target.value)}
                  />
                </td>
                <td className="border border-gray-300 px-4 py-2 text-right">
                  ${subtotal.toFixed(2)}
                </td>
              </tr>
            )
          })}
        </tbody>
        <tfoot>
          <tr className="bg-gray-100 font-semibold">
            <td colSpan={5} className="border border-gray-300 px-4 py-2 text-right">
              Costo Directo:
            </td>
            <td className="border border-gray-300 px-4 py-2 text-right">
              ${preview.costo_directo.toFixed(2)}
            </td>
          </tr>
          <tr className="bg-gray-100">
            <td colSpan={5} className="border border-gray-300 px-4 py-2 text-right">
              Indirectos (15%):
            </td>
            <td className="border border-gray-300 px-4 py-2 text-right">
              ${preview.indirectos.toFixed(2)}
            </td>
          </tr>
          <tr className="bg-gray-100">
            <td colSpan={5} className="border border-gray-300 px-4 py-2 text-right">
              Utilidad (10%):
            </td>
            <td className="border border-gray-300 px-4 py-2 text-right">
              ${preview.utilidad.toFixed(2)}
            </td>
          </tr>
          <tr className="bg-blue-100 font-bold">
            <td colSpan={5} className="border border-gray-300 px-4 py-2 text-right">
              Precio Unitario:
            </td>
            <td className="border border-gray-300 px-4 py-2 text-right">
              ${preview.precio_unitario.toFixed(2)}
            </td>
          </tr>
          <tr className="bg-blue-200 font-bold text-lg">
            <td colSpan={5} className="border border-gray-300 px-4 py-2 text-right">
              Importe Total:
            </td>
            <td className="border border-gray-300 px-4 py-2 text-right">
              ${preview.importe_total.toFixed(2)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
