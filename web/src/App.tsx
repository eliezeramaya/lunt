import { useState } from 'react'
import { apiClient, PreviewResponse } from '@/lib/api'
import { useDraft } from '@/store/useDraft'
import PriceBreakdownTable from '@/components/PriceBreakdownTable'
import LineSeries from '@/components/LineSeries'

function App() {
  const { draft, setDraft, adjustments, clearDraft } = useDraft()
  const [codigoConcepto, setCodigoConcepto] = useState('ALB-001')
  const [cantidad, setCantidad] = useState(100)
  const [locacionId, setLocacionId] = useState(1)
  const [loading, setLoading] = useState(false)
  const [showSeries, setShowSeries] = useState(false)
  const [seriesData, setSeriesData] = useState<any>(null)

  const handlePreview = async () => {
    setLoading(true)
    try {
      const response = await apiClient.preview({
        codigo_concepto: codigoConcepto,
        cantidad,
        locacion_id: locacionId,
      })
      setDraft(response)
    } catch (error) {
      console.error('Error fetching preview:', error)
      alert('Error al obtener la vista previa')
    } finally {
      setLoading(false)
    }
  }

  const handleRecalc = async () => {
    if (!draft) return
    setLoading(true)
    try {
      const response = await apiClient.recalc({
        codigo_concepto: codigoConcepto,
        cantidad,
        adjustments,
        locacion_id: locacionId,
      })
      setDraft(response)
    } catch (error) {
      console.error('Error recalculating:', error)
      alert('Error al recalcular')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    if (!draft) return
    setLoading(true)
    try {
      const response = await apiClient.confirm({
        codigo_concepto: codigoConcepto,
        cantidad,
        adjustments,
        user_id: 1,
        locacion_id: locacionId,
      })
      alert(`Cotización guardada con ID: ${response.quote_id}`)
      clearDraft()
    } catch (error) {
      console.error('Error confirming quote:', error)
      alert('Error al confirmar la cotización')
    } finally {
      setLoading(false)
    }
  }

  const handleShowSeries = async () => {
    setLoading(true)
    try {
      const response = await apiClient.conceptoSeries(codigoConcepto, cantidad, locacionId)
      setSeriesData(response)
      setShowSeries(true)
    } catch (error) {
      console.error('Error fetching series:', error)
      alert('Error al obtener la serie histórica')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-8">
          Lunt - Análisis de Costos de Construcción
        </h1>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">Nueva Cotización</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Código de Concepto
              </label>
              <input
                type="text"
                value={codigoConcepto}
                onChange={(e) => setCodigoConcepto(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Cantidad</label>
              <input
                type="number"
                value={cantidad}
                onChange={(e) => setCantidad(Number(e.target.value))}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Locación ID</label>
              <input
                type="number"
                value={locacionId}
                onChange={(e) => setLocacionId(Number(e.target.value))}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
          </div>
          <div className="flex gap-4">
            <button
              onClick={handlePreview}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? 'Cargando...' : 'Obtener Vista Previa'}
            </button>
            {draft && (
              <>
                <button
                  onClick={handleRecalc}
                  disabled={loading || Object.keys(adjustments).length === 0}
                  className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
                >
                  Recalcular
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={loading}
                  className="bg-purple-600 text-white px-6 py-2 rounded hover:bg-purple-700 disabled:bg-gray-400"
                >
                  Confirmar Cotización
                </button>
                <button
                  onClick={handleShowSeries}
                  disabled={loading}
                  className="bg-orange-600 text-white px-6 py-2 rounded hover:bg-orange-700 disabled:bg-gray-400"
                >
                  Ver Serie Histórica
                </button>
              </>
            )}
          </div>
        </div>

        {draft && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-2xl font-semibold mb-4">
              {draft.descripcion} ({draft.codigo_concepto})
            </h2>
            <p className="text-gray-600 mb-4">
              Unidad: {draft.unidad} | Cantidad: {draft.cantidad}
            </p>
            <PriceBreakdownTable preview={draft} />
          </div>
        )}

        {showSeries && seriesData && (
          <div className="bg-white rounded-lg shadow p-6">
            <LineSeries
              data={seriesData.series}
              title={`Serie Histórica: ${seriesData.descripcion} (${seriesData.codigo_concepto})`}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default App
