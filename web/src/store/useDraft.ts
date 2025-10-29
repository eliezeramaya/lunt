import { create } from 'zustand'
import { PreviewResponse, RecalcRequest } from '@/lib/api'

interface DraftState {
  draft: PreviewResponse | null
  adjustments: Record<string, number>
  setDraft: (draft: PreviewResponse) => void
  setAdjustment: (codigoInsumo: string, precio: number) => void
  clearDraft: () => void
  toRecalcRequest: (codigoConcepto: string, cantidad: number, locacionId?: number) => RecalcRequest
}

export const useDraft = create<DraftState>((set, get) => ({
  draft: null,
  adjustments: {},

  setDraft: (draft) => set({ draft, adjustments: {} }),

  setAdjustment: (codigoInsumo, precio) =>
    set((state) => ({
      adjustments: { ...state.adjustments, [codigoInsumo]: precio },
    })),

  clearDraft: () => set({ draft: null, adjustments: {} }),

  toRecalcRequest: (codigoConcepto, cantidad, locacionId) => {
    const { adjustments } = get()
    return {
      codigo_concepto: codigoConcepto,
      cantidad,
      adjustments,
      locacion_id: locacionId,
    }
  },
}))
