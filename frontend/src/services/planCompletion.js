/** Notify plan completion after coach activities (optional client-side helper). */

import { getTodayPlan, updatePlanItem } from '../api/client'

export function planItemsFromResponse(response) {
  return response?.plan_items_completed || []
}

export async function completePlanTrack(track) {
  try {
    const plan = await getTodayPlan()
    if (!plan?.exists || !plan.items) return []

    const item = plan.items.find((row) => row.id === `track-${track}` && !row.completed)
    if (!item) return []

    await updatePlanItem(item.id, true)
    return [item.id]
  } catch {
    return []
  }
}
